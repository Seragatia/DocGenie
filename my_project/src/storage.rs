// my_project/src/storage.rs
//! This module handles file storage operations for the downloader.
//! It provides functions to download files, ensure folders exist,
//! extract archives, transcode videos, and save download metadata.

use std::{
    error::Error,
    fs::{self, File},
    io::{self, BufWriter, Read, Write},
    path::{Path, PathBuf},
    process::Command,
};

use log::{debug, error, info};
use reqwest::blocking::{Client, Response};
use reqwest::header::RANGE;
use std::io::copy;
use zip::ZipArchive;

/// Sets up an HTTP client with default settings.
/// Customize timeouts, user agent, etc., as needed.
pub fn setup_connection(_url: &str) -> Result<Client, Box<dyn Error>> {
    let client = Client::new();
    info!("HTTP client created in storage.rs");
    Ok(client)
}

/// Downloads a file from the specified URL to the given file path,
/// optionally starting from a byte offset (for resume).
pub fn download_file(
    client: &Client,
    url: &str,
    file_path: &str,
    range_start: u64,
) -> Result<(), Box<dyn Error>> {
    let mut request = client.get(url);
    if range_start > 0 {
        let range_header = format!("bytes={}-", range_start);
        request = request.header(RANGE, range_header);
    }
    let mut response = request.send()?.error_for_status()?;

    // Create or truncate the file and write the response body.
    let file = File::create(file_path)?;
    let mut writer = BufWriter::new(file);
    copy(&mut response, &mut writer)?;
    writer.flush()?;
    info!("File downloaded to {}", file_path);
    Ok(())
}

/// Ensures the specified folder exists. If not, it creates the folder.
pub fn ensure_folder_exists(folder: &str) -> Result<(), Box<dyn Error>> {
    if !Path::new(folder).exists() {
        fs::create_dir_all(folder)?;
        info!("Folder created: {}", folder);
    } else {
        info!("Folder exists: {}", folder);
    }
    Ok(())
}

/// Saves download information (e.g., metadata) to a JSON file.
/// The `download_info` parameter can be any serializable value.
pub fn save_download_info(
    download_info: &serde_json::Value,
    file_path: &str,
) -> Result<(), Box<dyn Error>> {
    let file = File::create(file_path)?;
    serde_json::to_writer_pretty(file, download_info)?;
    info!("Download info saved to {}", file_path);
    Ok(())
}

/// Extracts a ZIP archive from `file_path` to the specified `destination` directory.
pub fn extract_archive(file_path: &str, destination: &str) -> Result<(), Box<dyn Error>> {
    let file = File::open(file_path)?;
    let mut archive = ZipArchive::new(file)?;
    fs::create_dir_all(destination)?;
    for i in 0..archive.len() {
        let mut file_in_zip = archive.by_index(i)?;
        let outpath = Path::new(destination).join(file_in_zip.name());
        if file_in_zip.is_dir() {
            fs::create_dir_all(&outpath)?;
        } else {
            if let Some(parent) = outpath.parent() {
                fs::create_dir_all(parent)?;
            }
            let mut outfile = File::create(&outpath)?;
            copy(&mut file_in_zip, &mut outfile)?;
        }
    }
    info!("Archive extracted to '{}'", destination);
    Ok(())
}

/// Transcodes a video file at `file_path` to the `target_format` using FFmpeg.
/// Assumes that FFmpeg is installed and available in the system's PATH.
pub fn transcode_video(file_path: &str, target_format: &str) -> Result<(), Box<dyn Error>> {
    let input_path = Path::new(file_path);
    let output_filename = input_path
        .file_stem()
        .and_then(|s| s.to_str())
        .map(|s| format!("{}_converted.{}", s, target_format))
        .ok_or("Failed to generate output filename")?;
    let output_path = input_path.with_file_name(output_filename);

    let status = Command::new("ffmpeg")
        .arg("-i")
        .arg(file_path)
        .arg("-c:v")
        .arg("libx264")
        .arg("-preset")
        .arg("fast")
        .arg("-c:a")
        .arg("aac")
        .arg(output_path.to_str().unwrap())
        .status()?;

    if status.success() {
        info!("Video transcoded successfully to '{}'", output_path.display());
        Ok(())
    } else {
        Err(Box::new(io::Error::new(
            io::ErrorKind::Other,
            "FFmpeg transcoding failed",
        )))
    }
}

/// Validates that a file at `file_path` exists and is non-empty.
pub fn validate_file(file_path: &str) -> bool {
    if let Ok(metadata) = fs::metadata(file_path) {
        metadata.len() > 0
    } else {
        false
    }
}
