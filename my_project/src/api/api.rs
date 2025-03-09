// my_project/src/api/api.rs
// This module defines the API routes and handlers for the download manager.
// It also defines the shared application state and helper functions for managing download tasks.

use actix_web::{get, post, web, HttpResponse, Responder, Result};
use serde::{Deserialize, Serialize};
use std::{
    collections::HashMap,
    sync::{Arc, RwLock},
    thread,
    time::Duration, // Added missing import for Duration
};
use log::{info, error, debug};

/// Represents the state of a single download task.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DownloadTask {
    pub id: String,
    pub url: String,
    pub destination: String,
    pub status: String, // e.g., "pending", "downloading", "paused", "completed", "failed"
    pub progress: f32,  // Progress percentage (0.0 to 100.0)
    pub segments: Option<usize>, // For segmented downloads (optional)
}

/// Shared application state containing active download tasks.
/// In a real scenario, you might store these in a database.
pub type AppState = Arc<RwLock<HashMap<String, DownloadTask>>>;

/// Health check endpoint.
/// Returns a simple message indicating that the backend is running.
#[get("/health")]
pub async fn health_check() -> impl Responder {
    info!("Health check endpoint was hit.");
    HttpResponse::Ok().body("Rust Backend is Running!")
}

/// Set this flag to true to simulate downloads for testing purposes.
/// When false, you would call your actual download logic.
const SIMULATE_DOWNLOAD: bool = true;

/// Starts a new download task by receiving a JSON payload and inserting it into shared state.
/// Then spawns a background thread to perform the download process.
#[post("/download")]
pub async fn start_download(
    data: web::Data<AppState>,
    task_req: web::Json<DownloadTask>,
) -> Result<impl Responder> {
    let mut state = data.write().map_err(|e| {
        error!("State write lock error: {}", e);
        actix_web::error::ErrorInternalServerError("Internal Server Error")
    })?;

    // Build a new DownloadTask from the request.
    let mut new_task = task_req.into_inner();
    if new_task.id.is_empty() {
        // Generate an ID if none is provided.
        new_task.id = format!("task-{}", state.len() + 1);
    }
    new_task.status = "pending".to_string();
    new_task.progress = 0.0;
    let task_id = new_task.id.clone();
    info!("Starting new download with task_id: {}", task_id);

    // Extract needed fields before moving new_task into shared state.
    let _url = new_task.url.clone();
    let _destination = new_task.destination.clone();
    let _segments = new_task.segments.unwrap_or(1);

    // Insert the new task into shared state.
    state.insert(task_id.clone(), new_task);

    // Clone shared state and task_id for use in the background thread.
    let data_clone = data.clone();
    let task_id_for_thread = task_id.clone();

    // Spawn a background thread to perform the download.
    thread::spawn(move || {
        // Define a progress callback that updates the shared state.
        let _progress_callback = {
            let data_clone = data_clone.clone();
            let task_id_for_thread = task_id_for_thread.clone();
            move |downloaded_bytes: u64, total_bytes: u64| {
                if let Ok(mut st) = data_clone.write() {
                    if let Some(task) = st.get_mut(&task_id_for_thread) {
                        if total_bytes > 0 {
                            let percent = (downloaded_bytes as f64 / total_bytes as f64) * 100.0;
                            task.progress = percent as f32;
                        } else {
                            task.progress = 0.0;
                        }
                        debug!("Task {} progress: {:.2}%", task_id_for_thread, task.progress);
                    }
                }
            }
        };

        // Mark the task as "downloading".
        if let Ok(mut st) = data_clone.write() {
            if let Some(task) = st.get_mut(&task_id_for_thread) {
                task.status = "downloading".to_string();
            }
        }

        // Simulate download if flag is true; replace with real download logic as needed.
        let res: Result<(), Box<dyn std::error::Error>> = if SIMULATE_DOWNLOAD {
            thread::sleep(Duration::from_secs(5));
            Ok(())
        } else {
            // When integrating real download logic, replace with calls to your download module.
            Ok(())
        };

        // Update the shared state based on the download result.
        if let Ok(mut st) = data_clone.write() {
            if let Some(task) = st.get_mut(&task_id_for_thread) {
                match res {
                    Ok(_) => {
                        info!("Task {} completed successfully.", task_id_for_thread);
                        task.status = "completed".to_string();
                        task.progress = 100.0;
                    }
                    Err(e) => {
                        error!("Task {} failed: {}", task_id_for_thread, e);
                        task.status = "failed".to_string();
                        task.progress = 0.0;
                    }
                }
            }
        }
    });

    // Return a JSON response with the task ID.
    Ok(HttpResponse::Ok().json(serde_json::json!({
        "message": "Download started",
        "task_id": task_id
    })))
}

/// Retrieves the status of a specific download task.
#[get("/download/{id}")]
pub async fn get_download_status(
    data: web::Data<AppState>,
    task_id: web::Path<String>,
) -> Result<impl Responder> {
    let id = task_id.into_inner();
    let state = data.read().map_err(|e| {
        error!("State read lock error: {}", e);
        actix_web::error::ErrorInternalServerError("Internal Server Error")
    })?;
    if let Some(task) = state.get(&id) {
        Ok(HttpResponse::Ok().json(task))
    } else {
        error!("Download task with id {} not found", id);
        Ok(HttpResponse::NotFound().json(serde_json::json!({
            "error": "Task not found"
        })))
    }
}

/// Pauses a specific download task (status change in memory only).
#[post("/download/{id}/pause")]
pub async fn pause_download(
    data: web::Data<AppState>,
    task_id: web::Path<String>,
) -> Result<impl Responder> {
    let id = task_id.into_inner();
    let mut state = data.write().map_err(|e| {
        error!("State write lock error: {}", e);
        actix_web::error::ErrorInternalServerError("Internal Server Error")
    })?;
    if let Some(task) = state.get_mut(&id) {
        task.status = "paused".to_string();
        info!("Paused download task: {}", task.id);
        Ok(HttpResponse::Ok().json(serde_json::json!({
            "message": "Download paused",
            "task_id": task.id,
        })))
    } else {
        error!("Download task with id {} not found", id);
        Ok(HttpResponse::NotFound().json(serde_json::json!({
            "error": "Task not found"
        })))
    }
}

/// Resumes a specific download task (status change only).
#[post("/download/{id}/resume")]
pub async fn resume_download(
    data: web::Data<AppState>,
    task_id: web::Path<String>,
) -> Result<impl Responder> {
    let id = task_id.into_inner();
    let mut state = data.write().map_err(|e| {
        error!("State write lock error: {}", e);
        actix_web::error::ErrorInternalServerError("Internal Server Error")
    })?;
    if let Some(task) = state.get_mut(&id) {
        task.status = "downloading".to_string();
        info!("Resumed download task: {}", task.id);
        Ok(HttpResponse::Ok().json(serde_json::json!({
            "message": "Download resumed",
            "task_id": task.id,
        })))
    } else {
        error!("Download task with id {} not found", id);
        Ok(HttpResponse::NotFound().json(serde_json::json!({
            "error": "Task not found"
        })))
    }
}

/// Cancels a download task by removing it from shared state.
/// Note: This does not kill a running download thread.
#[post("/download/{id}/cancel")]
pub async fn cancel_download(
    data: web::Data<AppState>,
    task_id: web::Path<String>,
) -> Result<impl Responder> {
    let id = task_id.into_inner();
    let mut state = data.write().map_err(|e| {
        error!("State write lock error: {}", e);
        actix_web::error::ErrorInternalServerError("Internal Server Error")
    })?;
    if state.remove(&id).is_some() {
        info!("Cancelled download task with id: {}", id);
        Ok(HttpResponse::Ok().json(serde_json::json!({
            "message": "Download canceled"
        })))
    } else {
        error!("Download task with id {} not found", id);
        Ok(HttpResponse::NotFound().json(serde_json::json!({
            "error": "Task not found"
        })))
    }
}

/// Lists all current download tasks.
#[get("/downloads")]
pub async fn list_downloads(data: web::Data<AppState>) -> Result<impl Responder> {
    let state = data.read().map_err(|e| {
        error!("State read lock error: {}", e);
        actix_web::error::ErrorInternalServerError("Internal Server Error")
    })?;
    let tasks: Vec<&DownloadTask> = state.values().collect();
    Ok(HttpResponse::Ok().json(tasks))
}

/// Configures the API routes under the "/api" scope.
pub fn configure_api(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/api")
            .service(start_download)
            .service(get_download_status)
            .service(pause_download)
            .service(resume_download)
            .service(cancel_download)
            .service(list_downloads),
    );
}
