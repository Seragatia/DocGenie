use reqwest::{Client, Response};
use std::{fs::{File, OpenOptions}, io::{self, Read, Write}, time::Duration};
use std::path::Path;
use std::error::Error;
use serde::{Serialize, Deserialize};
use rand::Rng;
use tokio::time::sleep;

#[derive(Serialize, Deserialize, Debug)]
pub struct DownloadState {
    pub url: String,
    pub file_path: String,
    pub downloaded_bytes: u64,
    pub total_size: u64,
}

impl DownloadState {
    // Save the current download state to a file for resumption
    pub fn save(&self) -> Result<(), io::Error> {
        let file = File::create("download_state.json")?;
        serde_json::to_writer(file, &self)?;
        Ok(())
    }

    // Load the saved download state
    pub fn load() -> Result<Self, io::Error> {
        let file = File::open("download_state.json")?;
        let state: DownloadState = serde_json::from_reader(file)?;
        Ok(state)
    }
}

pub struct Downloader {
    client: Client,
    max_retries: u32,
    base_delay: u64,  // Base delay for exponential backoff in seconds
}

impl Downloader {
    // Constructor for Downloader struct
    pub fn new(max_retries: u32, base_delay: u64) -> Self {
        Downloader {
            client: Client::new(),
            max_retries,
            base_delay,
        }
    }

    // Detect network failures and handle retries
    async fn retry_download(&self, url: &str, file_path: &str, range_start: u64) -> Result<(), Box<dyn Error>> {
        let mut retries = 0;

        loop {
            match self.download_file(url, file_path, range_start).await {
                Ok(_) => return Ok(()),
                Err(e) => {
                    eprintln!("Download failed: {}. Retrying...", e);
                    retries += 1;
                    if retries >= self.max_retries {
                        return Err(Box::new(io::Error::new(io::ErrorKind::Other, "Max retries reached")));
                    }

                    // Exponential backoff with jitter
                    let delay = self.exponential_backoff(retries);
                    sleep(delay).await;
                }
            }
        }
    }

    // Calculate the delay based on exponential backoff with jitter
    fn exponential_backoff(&self, retries: u32) -> Duration {
        let base_delay = self.base_delay * 2u64.pow(retries);
        let max_delay = 60;  // Max backoff time of 60 seconds
        let delay = std::cmp::min(base_delay, max_delay);
        let jitter = rand::thread_rng().gen_range(0..delay / 2);
        Duration::from_secs(delay + jitter)
    }

    // Download the file with support for resumption using HTTP Range header
    async fn download_file(&self, url: &str, file_path: &str, range_start: u64) -> Result<(), Box<dyn Error>> {
        let response = self.client
            .get(url)
            .header("Range", format!("bytes={}-", range_start))
            .send()
            .await?;

        if !response.status().is_success() {
            return Err(Box::new(io::Error::new(io::ErrorKind::Other, "Failed to fetch file")));
        }

        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(file_path)?;

        let total_size = response
            .headers()
            .get("Content-Range")
            .ok_or("Missing Content-Range header")?
            .to_str()?
            .split('/')
            .nth(1)
            .unwrap()
            .parse::<u64>()?;

        let mut downloaded = 0u64;
        let mut buffer = Vec::new();
        let mut content = response.bytes_stream();

        // Write received chunks to disk
        while let Some(chunk) = content.next().await {
            let data = chunk?;
            downloaded += data.len() as u64;
            buffer.extend_from_slice(&data);

            file.write_all(&data)?;
            eprintln!("Downloaded {} bytes out of {}", downloaded, total_size);
        }

        // Save download state after completion
        let state = DownloadState {
            url: url.to_string(),
            file_path: file_path.to_string(),
            downloaded_bytes: downloaded,
            total_size,
        };
        state.save()?;

        Ok(())
    }

    // Start the download or resume from saved state
    pub async fn start_or_resume_download(&self, url: &str, file_path: &str) -> Result<(), Box<dyn Error>> {
        let mut downloaded_bytes = 0;
        let total_size = 1000000000;  // Placeholder for file size, modify as needed

        // Check if there is a saved download state
        if Path::new("download_state.json").exists() {
            let state = DownloadState::load()?;
            if state.url == url {
                downloaded_bytes = state.downloaded_bytes;
                eprintln!("Resuming download from {} bytes", downloaded_bytes);
            }
        }

        // Start or resume download
        self.retry_download(url, file_path, downloaded_bytes).await
    }
}
