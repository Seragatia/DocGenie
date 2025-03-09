// src/api/metadata.rs

use actix_web::{post, web, HttpResponse, Responder, Result};
use serde::{Deserialize, Serialize};
use reqwest::header::{CONTENT_LENGTH, CONTENT_TYPE, CONTENT_DISPOSITION, HeaderMap};
use reqwest::Client;
use log::{info, error, debug};

/// Payload sent by the client (e.g., Python GUI) with the URL to inspect.
#[derive(Debug, Deserialize)]
pub struct UrlPayload {
    pub url: String,
}

/// Metadata about the file (size, content type, suggested file name).
#[derive(Debug, Serialize)]
pub struct FileMetadata {
    pub file_size: Option<u64>,
    pub content_type: Option<String>,
    pub suggested_name: Option<String>,
}

/// Endpoint: POST /api/metadata
/// The client sends a JSON payload with a URL and this endpoint returns file metadata.
#[post("/metadata")]
pub async fn get_file_metadata(
    payload: web::Json<UrlPayload>,
) -> impl Responder {
    let url = payload.url.clone();
    info!("Fetching metadata for URL: {}", url);

    match fetch_metadata(&url).await {
        Ok(meta) => HttpResponse::Ok().json(meta),
        Err(e) => {
            error!("Failed to fetch metadata for {}: {}", url, e);
            HttpResponse::BadRequest().json(serde_json::json!({
                "error": format!("Could not retrieve metadata: {}", e),
            }))
        }
    }
}

/// Performs a HEAD request to gather file metadata.
/// Returns a FileMetadata struct on success.
async fn fetch_metadata(url: &str) -> Result<FileMetadata, Box<dyn std::error::Error>> {
    // Build a client with a 10-second timeout.
    let client = Client::builder()
        .timeout(std::time::Duration::from_secs(10))
        .build()?;
    
    debug!("Sending HEAD request to {}", url);
    let resp = client.head(url).send().await?;
    if !resp.status().is_success() {
        let err_msg = format!("HTTP request failed with status: {}", resp.status());
        error!("{}", err_msg);
        return Err(err_msg.into());
    }
    debug!("HEAD request succeeded, processing headers.");

    let headers = resp.headers();
    let file_size = parse_content_length(headers);
    let content_type = parse_content_type(headers);
    let suggested_name = guess_file_name_from_url(url, headers);

    Ok(FileMetadata {
        file_size,
        content_type,
        suggested_name,
    })
}

/// Parses the Content-Length header from the response headers.
fn parse_content_length(headers: &HeaderMap) -> Option<u64> {
    headers.get(CONTENT_LENGTH)
        .and_then(|val| val.to_str().ok())
        .and_then(|s| s.parse::<u64>().ok())
}

/// Parses the Content-Type header from the response headers.
fn parse_content_type(headers: &HeaderMap) -> Option<String> {
    headers.get(CONTENT_TYPE)
        .and_then(|val| val.to_str().ok())
        .map(|s| s.to_string())
}

/// Attempts to guess a file name from the Content-Disposition header.
/// If not present, falls back to using the last segment of the URL path.
fn guess_file_name_from_url(url: &str, headers: &HeaderMap) -> Option<String> {
    if let Some(disposition) = headers.get(CONTENT_DISPOSITION) {
        if let Ok(val) = disposition.to_str() {
            if let Some(fname) = val.split("filename=").nth(1) {
                let fname_clean = fname.trim_matches('"').to_string();
                debug!("Extracted filename '{}' from Content-Disposition.", fname_clean);
                return Some(fname_clean);
            }
        }
    }
    let fallback = url.split('/').last().filter(|s| !s.is_empty()).map(|s| s.to_string());
    if let Some(ref name) = fallback {
        debug!("Falling back to filename '{}' extracted from URL.", name);
    } else {
        debug!("No filename could be extracted from URL.");
    }
    fallback
}

/// Configures the metadata endpoint under the "/api" scope.
pub fn configure_metadata(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/api")
            .service(get_file_metadata)
    );
}
