//! Module for handling interruptions and resumable downloads.
//! This module provides functionality to save and load download state,
//! and defines a Downloader struct that supports retrying downloads with
//! exponential backoff and resuming from a saved state.

use reqwest::{Client, Response};
use std::{
    fs::{File, OpenOptions},
    io::{self, Write},
    path::Path,
    time::Duration,
    error::Error,
};
use serde::{Serialize, Deserialize};
use rand::Rng;
use tokio::time::sleep;
use futures::StreamExt;
use log::{info, error, debug};

#[derive(Serialize, Deserialize, Debug)]
pub struct DownloadState {
    pub url: String,
    pub file_path: String,
    pub downloaded_bytes: u64,
    pub total_size: u64,
}

impl DownloadState {
    /// Saves the current download state to "download_state.json".
    pub fn save(&self) -> Result<(), io::Error> {
        let file = File::create("download_state.json")?;
        serde_json::to_writer(file, &self)?;
        info!("Download state saved to 'download_state.json'.");
        Ok(())
    }

    /// Loads the saved download state from "download_state.json".
    pub fn load() -> Result<Self, io::Error> {
        let file = File::open("download_state.json")?;
        let state: DownloadState = serde_json::from_reader(file)?;
        info!("Download state loaded from 'download_state.json'.");
        Ok(state)
    }
}

pub struct Downloader {
    client: Client,
    max_retries: u32,
    base_delay: u64, // Base delay for exponential backoff (in seconds)
}

impl Downloader {
    /// Creates a new Downloader instance.
    pub fn new(max_retries: u32, base_delay: u64) -> Self {
        Self {
            client: Client::new(),
            max_retries,
            base_delay,
        }
    }

    /// Retries the download until successful or maximum retries are reached.
    pub async fn retry_download(&self, url: &str, file_path: &str, range_start: u64) -> Result<(), Box<dyn Error>> {
        let mut retries = 0;
        loop {
            match self.download_file(url, file_path, range_start).await {
                Ok(_) => {
                    info!("Download succeeded.");
                    return Ok(());
                }
                Err(e) => {
                    error!("Download failed: {}. Retrying...", e);
                    retries += 1;
                    if retries >= self.max_retries {
                        error!("Max retries reached.");
                        return Err(Box::new(io::Error::new(io::ErrorKind::Other, "Max retries reached")));
                    }
                    let delay = self.exponential_backoff(retries);
                    info!("Waiting {:?} before next retry...", delay);
                    sleep(delay).await;
                }
            }
        }
    }

    /// Calculates the exponential backoff delay with jitter.
    fn exponential_backoff(&self, retries: u32) -> Duration {
        let base_delay = self.base_delay * 2u64.pow(retries);
        let max_delay = 60; // maximum backoff of 60 seconds
        let delay = std::cmp::min(base_delay, max_delay);
        let jitter = rand::thread_rng().gen_range(0..delay / 2);
        Duration::from_secs(delay + jitter)
    }

    /// Downloads the file from the given URL, starting at `range_start` bytes,
    /// writing data to `file_path`, and updating progress via the provided callback.
    pub async fn download_file(&self, url: &str, file_path: &str, range_start: u64) -> Result<(), Box<dyn Error>> {
        let response = self.client
            .get(url)
            .header("Range", format!("bytes={}-", range_start))
            .send()
            .await?;

        if !response.status().is_success() {
            return Err(Box::new(io::Error::new(io::ErrorKind::Other, "Failed to fetch file")));
        }

        // Open the file in append mode (for resumption).
        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(file_path)?;

        // Try to extract the total file size from the "Content-Range" header.
        let total_size = if let Some(range_header) = response.headers().get("Content-Range") {
            if let Ok(range_str) = range_header.to_str() {
                range_str.split('/').nth(1)
                    .and_then(|s| s.parse::<u64>().ok())
                    .unwrap_or(0)
            } else {
                0
            }
        } else {
            0
        };

        let mut downloaded = range_start; // start from the given offset
        let mut stream = response.bytes_stream();

        while let Some(chunk) = stream.next().await {
            let data = chunk?;
            file.write_all(&data)?;
            downloaded += data.len() as u64;
            info!("Downloaded {} bytes out of {}", downloaded, total_size);
        }

        // Save download state for resumption.
        let state = DownloadState {
            url: url.to_string(),
            file_path: file_path.to_string(),
            downloaded_bytes: downloaded,
            total_size,
        };
        state.save()?;

        Ok(())
    }

    /// Starts a download or resumes from a saved state.
    pub async fn start_or_resume_download(&self, url: &str, file_path: &str) -> Result<(), Box<dyn Error>> {
        let mut downloaded_bytes = 0;
        if Path::new("download_state.json").exists() {
            let state = DownloadState::load()?;
            if state.url == url {
                downloaded_bytes = state.downloaded_bytes;
                info!("Resuming download from {} bytes", downloaded_bytes);
            }
        }
        self.retry_download(url, file_path, downloaded_bytes).await
    }
}
