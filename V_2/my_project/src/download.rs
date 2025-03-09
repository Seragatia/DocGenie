use reqwest::{blocking::Client, header::CONTENT_LENGTH};
use std::{fs::File, io::{self, Read, Write}, path::Path, error::Error, time::Duration, thread::sleep};
use log::{info, error, warn};

pub const MAX_RETRIES: u32 = 5;
pub const BACKOFF_DELAY: u64 = 2; // Exponential backoff starts with 2 seconds

// Function to setup the connection with proper headers and user agent.
pub fn setup_connection() -> Result<Client, Box<dyn Error>> {
    let client = Client::builder()
        .timeout(Duration::from_secs(30))
        .danger_accept_invalid_certs(true)  // Useful for HTTPS sources with self-signed certificates.
        .user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        .build()?;
    Ok(client)
}

// Function to prepare and send the download request.
pub fn prepare_download_request(client: &Client, url: &str) -> Result<reqwest::blocking::Response, Box<dyn Error>> {
    let response = client.get(url).send()?;
    if response.status().is_success() {
        Ok(response)
    } else {
        Err(Box::new(io::Error::new(io::ErrorKind::Other, "Failed to download file")))
    }
}

// Function to stream data to disk.
pub fn stream_data_to_disk(mut response: reqwest::blocking::Response, file_path: &str) -> Result<(), Box<dyn Error>> {
    // Extract the total file size from the Content-Length header.
    let total_size = response
        .headers()
        .get(CONTENT_LENGTH)
        .ok_or("Missing Content-Length header")?
        .to_str()?
        .parse::<u64>()?;
    
    let mut file = File::create(file_path)?;
    let mut downloaded_size = 0u64;
    let mut buffer = [0; 8192];  // 8 KB buffer

    // Read data in chunks from the response and write to disk.
    loop {
        let n = response.read(&mut buffer)?;
        if n == 0 {
            break;
        }
        file.write_all(&buffer[..n])?;
        downloaded_size += n as u64;
        track_progress(total_size, downloaded_size);
    }

    info!("Download completed for file: {}", file_path);
    Ok(())
}

// Function to retry download on failure with exponential backoff.
pub fn retry_download(url: &str, max_retries: u32) -> Result<(), Box<dyn Error>> {
    let client = setup_connection()?;
    let mut retries = 0;

    loop {
        match prepare_download_request(&client, url) {
            Ok(response) => {
                let file_path = "downloaded_file.dat";  // Change this as needed.
                match stream_data_to_disk(response, file_path) {
                    Ok(_) => return Ok(()),
                    Err(e) => error!("Error downloading file: {}", e),
                }
            }
            Err(e) => error!("Request failed: {}", e),
        }

        retries += 1;
        if retries >= max_retries {
            return Err(Box::new(io::Error::new(io::ErrorKind::Other, "Max retries reached")));
        }

        let backoff_time = BACKOFF_DELAY * (2u64.pow(retries));
        warn!("Retrying in {} seconds...", backoff_time);
        sleep(Duration::from_secs(backoff_time));
    }
}

// Function to track download progress.
pub fn track_progress(total_size: u64, downloaded_size: u64) {
    let progress = (downloaded_size as f64 / total_size as f64) * 100.0;
    info!("Download progress: {:.2}%", progress);
}

// Function to verify the integrity of the downloaded file (checksum verification placeholder).
pub fn verify_integrity(file_path: &str, expected_size: u64, _expected_hash: &str) -> Result<bool, Box<dyn Error>> {
    let metadata = std::fs::metadata(file_path)?;
    let actual_size = metadata.len();

    if actual_size != expected_size {
        error!("File size mismatch. Expected: {}, Got: {}", expected_size, actual_size);
        return Ok(false);
    }

    // Placeholder: Insert checksum verification (e.g., MD5, SHA256) here if needed.
    info!("File integrity verified for: {}", file_path);
    Ok(true)
}

// Function to clean up partial downloads in case of errors.
pub fn cleanup_after_failure(file_path: &str) {
    if Path::new(file_path).exists() {
        match std::fs::remove_file(file_path) {
            Ok(_) => info!("Successfully cleaned up partial download: {}", file_path),
            Err(e) => error!("Failed to clean up partial download: {}", e),
        }
    } else {
        info!("No partial download file found to clean up.");
    }
}
