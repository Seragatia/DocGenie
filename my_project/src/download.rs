//! Module for downloading files from the web with support for segmented downloads
//! and real‑time progress tracking.
//my_project/src/download.rs
use log::{debug, error, info};
use reqwest::{
    blocking::{Client, Response},
    header::{CONTENT_LENGTH, RANGE},
};
use std::{
    fs::{File, remove_file},
    io::{self, Read, Write},
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicU64, Ordering},
        Arc, Mutex,
    },
    thread,
    thread::sleep,
    time::Duration,
};
use url::Url; // Make sure you have "url = \"2.2\"" in Cargo.toml

/// Maximum number of retries for a download.
pub const MAX_RETRIES: u32 = 5;
/// Base backoff time in seconds.
pub const BACKOFF_DELAY: u64 = 2;

/// Sets up an HTTP client with a 30‑second timeout, accepting invalid certificates (for testing)
/// and using a custom user agent.
pub fn setup_connection() -> Result<Client, Box<dyn std::error::Error>> {
    let client = Client::builder()
        .timeout(Duration::from_secs(30))
        .danger_accept_invalid_certs(true)
        .user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                     AppleWebKit/537.36 (KHTML, Gecko) \
                     Chrome/91.0.4472.124 Safari/537.36")
        .build()?;
    info!("HTTP client setup complete.");
    Ok(client)
}

/// Sends a GET request to the specified URL and returns the response if successful.
pub fn prepare_download_request(
    client: &Client,
    url: &str,
) -> Result<Response, Box<dyn std::error::Error>> {
    info!("Preparing download request for URL: {}", url);
    let response = client.get(url).send()?;
    if response.status().is_success() {
        info!("Download request for {} succeeded.", url);
        Ok(response)
    } else {
        let status = response.status();
        let error_msg = format!("HTTP request failed with status: {}", status);
        error!("{}", error_msg);
        Err(Box::new(io::Error::new(io::ErrorKind::Other, error_msg)))
    }
}

/// Resolves the final file path. If `file_path` is a directory (or does not have an extension),
/// attempts to extract a file name from the URL. If extraction fails or the resulting path is still a directory,
/// appends the default name "downloaded_file". This ensures that the returned path does not point to a directory.
fn resolve_file_path(url: &str, file_path: &str) -> PathBuf {
    let mut path = PathBuf::from(file_path);

    // Determine whether to treat the provided path as a directory:
    // If the path exists, check if it's a directory; if it does not exist, assume it's a directory if no file extension is present.
    let treat_as_directory = if path.exists() {
        path.is_dir()
    } else {
        path.extension().is_none()
    };

    if treat_as_directory {
        debug!("Provided path '{}' is treated as a directory.", file_path);
        // Attempt to extract a filename from the URL.
        if let Ok(parsed_url) = Url::parse(url) {
            if let Some(filename) = parsed_url
                .path_segments()
                .and_then(|segments| segments.last())
                .filter(|s| !s.is_empty())
            {
                // Append the extracted filename.
                path.push(filename);
                debug!("Extracted filename '{}' from URL; tentative path: {:?}", filename, path);
            }
        }
        // If the resulting path is still a directory (or no filename was extracted), append a default filename.
        if path.is_dir() || path.file_name().is_none() {
            path.push("downloaded_file");
            debug!("Appended default filename; final path: {:?}", path);
        }
    } else {
        debug!("Using provided file path as full file name: {:?}", path);
    }

    path
}

/// Streams the response data to a file at the specified path while triggering a progress callback.
/// The callback receives (downloaded_bytes, total_bytes).
pub fn stream_data_to_disk<F>(
    mut response: Response,
    file_path: &Path,
    progress_callback: Arc<F>,
) -> Result<(), Box<dyn std::error::Error>>
where
    F: Fn(u64, u64) + Send + Sync + 'static,
{
    let total_size = response
        .headers()
        .get(CONTENT_LENGTH)
        .and_then(|val| val.to_str().ok())
        .and_then(|s| s.parse::<u64>().ok())
        .unwrap_or(0);

    let mut file = File::create(file_path)?;
    let mut buffer = [0; 8192];
    let mut downloaded_size = 0u64;

    loop {
        let n = response.read(&mut buffer)?;
        if n == 0 {
            break;
        }
        file.write_all(&buffer[..n])?;
        downloaded_size += n as u64;

        // Trigger the progress callback.
        progress_callback(downloaded_size, total_size);

        if total_size > 0 {
            let progress = (downloaded_size as f64 / total_size as f64) * 100.0;
            debug!("Downloaded {:.2}% ({} / {} bytes)", progress, downloaded_size, total_size);
        } else {
            debug!("Downloaded {} bytes so far", downloaded_size);
        }
    }

    info!("Download completed for file: {:?}", file_path);
    Ok(())
}

/// Convenience function that sets up a client, sends a request, and streams data to disk,
/// updating progress via the provided callback. It uses `resolve_file_path` to ensure that if a directory
/// is provided, a valid file path is generated.
pub fn start_download<F>(
    url: &str,
    file_path: &str,
    progress_callback: F,
) -> Result<(), Box<dyn std::error::Error>>
where
    F: Fn(u64, u64) + Send + Sync + 'static,
{
    let final_path = resolve_file_path(url, file_path);
    info!("Starting download from {} to {:?}", url, final_path);
    let client = setup_connection()?;
    let response = prepare_download_request(&client, url)?;
    let callback = Arc::new(progress_callback);

    stream_data_to_disk(response, &final_path, callback)?;
    info!("Successfully downloaded file to {:?}", final_path);
    Ok(())
}

/// Retries a download up to `max_retries` times with exponential backoff.
pub fn retry_download<F>(
    url: &str,
    file_path: &str,
    max_retries: u32,
    progress_callback: F,
) -> Result<(), Box<dyn std::error::Error>>
where
    F: Fn(u64, u64) + Send + Sync + 'static,
{
    let final_path = resolve_file_path(url, file_path);
    let client = setup_connection()?;
    let callback = Arc::new(progress_callback);
    let mut retries = 0;

    loop {
        let result = prepare_download_request(&client, url)
            .and_then(|resp| stream_data_to_disk(resp, &final_path, Arc::clone(&callback)));

        match result {
            Ok(_) => return Ok(()),
            Err(e) => error!("Error downloading file: {}", e),
        }

        retries += 1;
        if retries >= max_retries {
            return Err(Box::new(io::Error::new(io::ErrorKind::Other, "Max retries reached")));
        }

        let backoff_time = BACKOFF_DELAY * (2u64.pow(retries));
        error!(
            "Retrying download in {} seconds... (attempt {}/{})",
            backoff_time, retries, max_retries
        );
        sleep(Duration::from_secs(backoff_time));
    }
}

/// Downloads a specific segment of the file and saves it to a temporary file.
/// (This function is currently unused; you may remove it if not needed.)
#[allow(dead_code)]
fn download_segment(
    client: &Client,
    url: &str,
    start: u64,
    end: u64,
    segment_index: usize,
) -> Result<String, Box<dyn std::error::Error>> {
    let range_header = format!("bytes={}-{}", start, end);
    debug!("Downloading segment {}: {}", segment_index, range_header);

    let response = client
        .get(url)
        .header(RANGE, range_header)
        .send()?
        .error_for_status()?;

    let temp_file = format!("segment_{}.tmp", segment_index);
    let mut file = File::create(&temp_file)?;
    let content = response.bytes()?;
    file.write_all(&content)?;

    Ok(temp_file)
}

/// Merges temporary segment files into the final output file and then removes the temporary files.
fn merge_segments(temp_files: &[String], output_file: &str) -> Result<(), Box<dyn std::error::Error>> {
    let mut output = File::create(output_file)?;
    for temp_file in temp_files {
        let mut part = File::open(temp_file)?;
        io::copy(&mut part, &mut output)?;
        remove_file(temp_file)?;
    }
    info!("Merged segments into {}", output_file);
    Ok(())
}

/// Downloads a file segment in small chunks, updating a shared AtomicU64 to track overall progress,
/// and calling the progress callback accordingly.
fn download_segment_in_chunks<F>(
    client: &Client,
    url: &str,
    start: u64,
    end: u64,
    segment_index: usize,
    downloaded_so_far: Arc<AtomicU64>,
    total_size: u64,
    progress_callback: Arc<F>,
) -> Result<String, Box<dyn std::error::Error>>
where
    F: Fn(u64, u64) + Send + Sync + 'static,
{
    let range_header = format!("bytes={}-{}", start, end);
    debug!("Downloading segment {}: {}", segment_index, range_header);

    let mut response = client
        .get(url)
        .header(RANGE, range_header)
        .send()?
        .error_for_status()?;

    let temp_file = format!("segment_{}.tmp", segment_index);
    let mut file = File::create(&temp_file)?;
    let mut buffer = [0; 8192];
    loop {
        let n = response.read(&mut buffer)?;
        if n == 0 {
            break;
        }
        file.write_all(&buffer[..n])?;

        // Update overall progress.
        let new_val = downloaded_so_far.fetch_add(n as u64, Ordering::SeqCst) + n as u64;
        progress_callback(new_val, total_size);

        if total_size > 0 {
            let progress_percent = (new_val as f64 / total_size as f64) * 100.0;
            debug!(
                "Segment {}: downloaded {} bytes, overall: {:.2}% ({} / {})",
                segment_index, n, progress_percent, new_val, total_size
            );
        } else {
            debug!(
                "Segment {}: downloaded {} bytes so far, total unknown",
                segment_index, new_val
            );
        }
    }
    Ok(temp_file)
}

/// Performs segmented downloading by splitting the file into `segments` parts.
/// If `segments` is less than 2 or the file size is unknown (0), it falls back to `start_download`.
pub fn segmented_download<F>(
    url: &str,
    file_path: &str,
    segments: usize,
    progress_callback: F,
) -> Result<(), Box<dyn std::error::Error>>
where
    F: Fn(u64, u64) + Send + Sync + 'static,
{
    let final_path = resolve_file_path(url, file_path);
    let client = setup_connection()?;
    let total_size = {
        let response = client.head(url).send()?;
        response
            .headers()
            .get(CONTENT_LENGTH)
            .and_then(|val| val.to_str().ok()?.parse::<u64>().ok())
            .unwrap_or(0)
    };

    // If segmented download is not feasible, fall back to a normal download.
    if segments < 2 || total_size == 0 {
        return start_download(url, final_path.to_str().unwrap(), progress_callback);
    }

    // Shared atomic counter to track overall downloaded bytes.
    let downloaded_so_far = Arc::new(AtomicU64::new(0));
    let callback = Arc::new(progress_callback);
    let segment_size = total_size / segments as u64;
    let temp_files = Arc::new(Mutex::new(Vec::new()));

    // Spawn threads for each segment using structured concurrency.
    thread::scope(|scope| {
        for i in 0..segments {
            let client_clone = client.clone();
            let url_clone = url.to_string();
            let temp_files_clone = Arc::clone(&temp_files);
            let start = i as u64 * segment_size;
            let end = if i == segments - 1 {
                total_size - 1
            } else {
                ((i + 1) as u64) * segment_size - 1
            };
            let downloaded_clone = Arc::clone(&downloaded_so_far);
            let cb_clone = Arc::clone(&callback);

            scope.spawn(move || {
                match download_segment_in_chunks(
                    &client_clone,
                    &url_clone,
                    start,
                    end,
                    i,
                    downloaded_clone,
                    total_size,
                    cb_clone,
                ) {
                    Ok(temp_file) => {
                        let mut files = temp_files_clone.lock().unwrap();
                        files.push(temp_file);
                    }
                    Err(e) => error!("Segment {} failed: {}", i, e),
                }
            });
        }
    });

    let temp_files = temp_files.lock().unwrap();
    merge_segments(&temp_files, final_path.to_str().unwrap())
}
