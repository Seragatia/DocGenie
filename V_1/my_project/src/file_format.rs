use std::error::Error;
use std::fs;
use std::io::{self, Write};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::fs::File;
use zip::ZipArchive;
use std::io::copy;

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

/// Main entry point for post-processing a downloaded file.
/// Based on the file type, it either extracts an archive or transcodes a video.
pub fn process_file(file_path: &str, destination: Option<&str>, target_format: Option<&str>) -> Result<(), Box<dyn Error>> {
    if is_zip_archive(file_path) {
        // Determine destination directory: use provided or the file's parent directory.
        let dest_dir = destination.unwrap_or_else(|| {
            Path::new(file_path).parent().unwrap_or_else(|| Path::new(".")).to_str().unwrap()
        });
        extract_archive(file_path, dest_dir)?;
    } else if is_video_file(file_path) {
        // Transcode video only if a target format is provided.
        if let Some(format) = target_format {
            transcode_video(file_path, format)?;
        } else {
            println!("No target format provided; skipping transcoding.");
        }
    } else {
        println!("File '{}' does not require post-processing.", file_path);
    }
    Ok(())
}

/// Extracts a ZIP archive to the specified destination directory.
pub fn extract_archive(file_path: &str, destination: &str) -> Result<(), Box<dyn Error>> {
    let file = File::open(file_path)?;
    let mut archive = ZipArchive::new(file)?;

    // Ensure destination directory exists.
    fs::create_dir_all(destination)?;

    // Extract each file in the archive.
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

    println!("Archive extracted to '{}'", destination);
    Ok(())
}

/// Transcodes a video file to the target format using FFmpeg.
/// This function assumes that FFmpeg is installed and available in the system's PATH.
pub fn transcode_video(file_path: &str, target_format: &str) -> Result<(), Box<dyn Error>> {
    let input_path = Path::new(file_path);
    let output_filename = input_path
        .file_stem()
        .and_then(|s| s.to_str())
        .map(|s| format!("{}_converted.{}", s, target_format))
        .ok_or("Failed to generate output filename")?;
    let output_path = input_path.with_file_name(output_filename);

    // Call FFmpeg to transcode the video.
    let status = Command::new("ffmpeg")
        .arg("-i")
        .arg(file_path)
        .arg("-c:v")
        .arg("libx264")    // Example video codec.
        .arg("-preset")
        .arg("fast")
        .arg("-c:a")
        .arg("aac")        // Example audio codec.
        .arg(output_path.to_str().unwrap())
        .status()?;

    if status.success() {
        println!("Video transcoded successfully to '{}'", output_path.display());
        Ok(())
    } else {
        Err(Box::new(io::Error::new(io::ErrorKind::Other, "FFmpeg transcoding failed")))
    }
}

/// Validates that a processed file exists and is non-empty.
/// This function can be extended with checksum verification if needed.
pub fn validate_file(file_path: &str) -> bool {
    if let Ok(metadata) = fs::metadata(file_path) {
        metadata.len() > 0
    } else {
        false
    }
}
