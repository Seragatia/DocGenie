use reqwest::{blocking::Client, header::{USER_AGENT, CONTENT_LENGTH}};
use std::{fs::File, io::{self, Write}, time::Duration};
use std::path::Path;
use std::error::Error;
use std::thread::sleep;

pub const MAX_RETRIES: u32 = 5;
pub const BACKOFF_DELAY: u64 = 2; // Exponential backoff starts with 2 seconds

// Function to setup the connection with proper headers and user agent
pub fn setup_connection(url: &str) -> Result<Client, Box<dyn Error>> {
    let client = Client::builder()
        .timeout(Duration::from_secs(30))
        .danger_accept_invalid_certs(true)  // For handling invalid SSL certificates, useful for some HTTPS sources
        .user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        .build()?;

    Ok(client)
}

// Function to prepare and send the download request
pub fn prepare_download_request(client: &Client, url: &str) -> Result<reqwest::blocking::Response, Box<dyn Error>> {
    let response = client.get(url)
        .send()?;

    if response.status().is_success() {
        Ok(response)
    } else {
        Err(Box::new(io::Error::new(io::ErrorKind::Other, "Failed to download file")))
    }
}

// Function to stream data to the disk
pub fn stream_data_to_disk(response: reqwest::blocking::Response, file_path: &str) -> Result<(), Box<dyn Error>> {
    let total_size = response
        .headers()
        .get(CONTENT_LENGTH)
        .ok_or("Missing Content-Length header")?
        .to_str()?
        .parse::<u64>()?;

    let mut file = File::create(file_path)?;
    let mut downloaded_size = 0u64;
    let mut buffer = [0u8; 8192]; // 8KB buffer

    // Reading data in chunks and writing to disk
    for chunk in response.bytes() {
        let chunk = chunk?;
        file.write_all(&chunk)?;
        downloaded_size += chunk.len() as u64;
        track_progress(total_size, downloaded_size);
    }

    Ok(())
}

// Function to retry download on failure with exponential backoff
pub fn retry_download(url: &str, max_retries: u32) -> Result<(), Box<dyn Error>> {
    let client = setup_connection(url)?;
    let mut retries = 0;

    loop {
        match prepare_download_request(&client, url) {
            Ok(response) => {
                let file_path = "downloaded_file.dat";  // Change to dynamic name if needed
                match stream_data_to_disk(response, file_path) {
                    Ok(_) => return Ok(()),
                    Err(e) => {
                        eprintln!("Error downloading file: {}", e);
                    }
                }
            }
            Err(e) => {
                eprintln!("Request failed: {}", e);
            }
        }

        retries += 1;
        if retries >= max_retries {
            return Err(Box::new(io::Error::new(io::ErrorKind::Other, "Max retries reached")));
        }

        // Exponential backoff
        let backoff_time = BACKOFF_DELAY * (2u64.pow(retries));
        eprintln!("Retrying in {} seconds...", backoff_time);
        sleep(Duration::from_secs(backoff_time));
    }
}

// Function to track download progress
pub fn track_progress(total_size: u64, downloaded_size: u64) {
    let progress = (downloaded_size as f64 / total_size as f64) * 100.0;
    println!("Download progress: {:.2}%", progress);
}

// Function to verify the integrity of the downloaded file (Checksum)
pub fn verify_integrity(file_path: &str, expected_size: u64, expected_hash: &str) -> bool {
    let metadata = std::fs::metadata(file_path).unwrap();
    let actual_size = metadata.len();

    if actual_size != expected_size {
        println!("File size mismatch. Expected: {}, Got: {}", expected_size, actual_size);
        return false;
    }

    // Here, you would implement checksum verification logic (e.g., MD5, SHA256)
    // For now, we assume the file is valid if the size matches
    true
}

// Function to clean up partial downloads in case of errors
pub fn cleanup_after_failure(file_path: &str) {
    if Path::new(file_path).exists() {
        std::fs::remove_file(file_path).unwrap_or_else(|e| {
            eprintln!("Failed to clean up partial download: {}", e);
        });
    }
}

