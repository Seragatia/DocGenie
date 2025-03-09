//! Module for processing downloaded files.
//! Supports extracting ZIP archives and transcoding video files.

use log::{debug, error, info};
use std::error::Error;
use std::fs;
use std::fs::File;
use std::io::{self, copy, Write};
use std::path::{Path, PathBuf};
use std::process::Command;
use url::Url; // Ensure "url = \"2.2\"" is in Cargo.toml
use zip::ZipArchive;

/// Returns true if the file extension indicates a ZIP archive.
fn is_zip_archive(file_path: &str) -> bool {
    Path::new(file_path)
        .extension()
        .map(|ext| ext.to_string_lossy().to_lowercase() == "zip")
        .unwrap_or(false)
}

/// Returns true if the file extension indicates a video file.
fn is_video_file(file_path: &str) -> bool {
    if let Some(ext) = Path::new(file_path).extension().and_then(|e| e.to_str()) {
        matches!(ext.to_lowercase().as_str(), "mp4" | "mkv" | "avi" | "mov" | "flv" | "wmv")
    } else {
        false
    }
}

/// Processes a downloaded file based on its type.
/// - If the file is a ZIP archive, extracts it to the destination.
/// - If it's a video file and a target format is provided, transcodes it.
/// - Otherwise, logs that no post‑processing is required.
///
/// # Arguments
/// * `file_path` - The path to the downloaded file.
/// * `destination` - Optional directory to extract to (if file is an archive).
/// * `target_format` - Optional target format (if file is a video).
pub fn process_file(
    file_path: &str,
    destination: Option<&str>,
    target_format: Option<&str>,
) -> Result<(), Box<dyn Error>> {
    if is_zip_archive(file_path) {
        info!("File '{}' is a ZIP archive. Starting extraction.", file_path);
        let dest_dir = destination.unwrap_or_else(|| {
            Path::new(file_path)
                .parent()
                .unwrap_or_else(|| Path::new("."))
                .to_str()
                .unwrap()
        });
        extract_archive(file_path, dest_dir)?;
    } else if is_video_file(file_path) {
        info!("File '{}' is a video file.", file_path);
        if let Some(format) = target_format {
            info!("Target format provided ({}). Starting transcoding.", format);
            transcode_video(file_path, format)?;
        } else {
            info!("No target format provided; skipping transcoding for '{}'.", file_path);
        }
    } else {
        info!("File '{}' does not require post‑processing.", file_path);
    }
    Ok(())
}

/// Resolves the final file path.
/// If `file_path` is a directory, attempts to extract a file name from the URL.
/// If extraction fails, defaults to "downloaded_file".
fn resolve_file_path(url: &str, file_path: &str) -> PathBuf {
    let path = Path::new(file_path);
    if path.is_dir() {
        debug!("'{}' is a directory; attempting to derive file name from URL.", file_path);
        if let Ok(parsed_url) = Url::parse(url) {
            if let Some(filename) = parsed_url
                .path_segments()
                .and_then(|segments| segments.last())
                .filter(|s| !s.is_empty())
            {
                let final_path = path.join(filename);
                debug!("Extracted file name '{}'. Final path: {:?}", filename, final_path);
                return final_path;
            }
        }
        let default_path = path.join("downloaded_file");
        debug!(
            "Could not extract file name from URL. Using default file name. Final path: {:?}",
            default_path
        );
        default_path
    } else {
        PathBuf::from(file_path)
    }
}

/// Extracts a ZIP archive to the specified destination directory.
pub fn extract_archive(file_path: &str, destination: &str) -> Result<(), Box<dyn Error>> {
    info!("Extracting archive '{}' to directory '{}'.", file_path, destination);
    let file = File::open(file_path)?;
    let mut archive = ZipArchive::new(file)?;

    // Ensure destination directory exists.
    fs::create_dir_all(destination)?;

    for i in 0..archive.len() {
        let mut file_in_zip = archive.by_index(i)?;
        let outpath = Path::new(destination).join(file_in_zip.name());

        if file_in_zip.is_dir() {
            fs::create_dir_all(&outpath)?;
            debug!("Created directory: {:?}", outpath);
        } else {
            if let Some(parent) = outpath.parent() {
                fs::create_dir_all(parent)?;
            }
            let mut outfile = File::create(&outpath)?;
            copy(&mut file_in_zip, &mut outfile)?;
            debug!("Extracted file to: {:?}", outpath);
        }
    }
    info!("Archive extracted to '{}'.", destination);
    Ok(())
}

/// Transcodes a video file to the target format using FFmpeg.
/// Assumes that FFmpeg is installed and available in PATH.
pub fn transcode_video(file_path: &str, target_format: &str) -> Result<(), Box<dyn Error>> {
    info!("Transcoding video '{}' to format '{}'.", file_path, target_format);
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
        .arg(output_path.to_str().ok_or("Invalid output path")?)
        .status()?;

    if status.success() {
        info!("Video transcoded successfully to '{}'.", output_path.display());
        Ok(())
    } else {
        let err_msg = format!("FFmpeg transcoding failed for '{}'.", file_path);
        error!("{}", err_msg);
        Err(Box::new(io::Error::new(io::ErrorKind::Other, err_msg)))
    }
}

/// Validates that a processed file exists and is non‑empty.
pub fn validate_file(file_path: &str) -> bool {
    match fs::metadata(file_path) {
        Ok(metadata) => {
            if metadata.len() > 0 {
                debug!("File '{}' is valid ({} bytes).", file_path, metadata.len());
                true
            } else {
                error!("File '{}' exists but is empty.", file_path);
                false
            }
        }
        Err(e) => {
            error!("Failed to get metadata for file '{}': {}", file_path, e);
            false
        }
    }
}
