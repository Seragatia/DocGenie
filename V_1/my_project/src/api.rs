// src/api.rs

use actix_web::{web, App, HttpResponse, HttpServer, Responder, Result};
use serde::{Deserialize, Serialize};
use std::{
    collections::HashMap,
    sync::{Arc, Mutex},
};

/// Represents the state of a single download task.
/// In a real implementation, you might store additional info
/// or even references to your internal download manager.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DownloadTask {
    pub id: String,
    pub url: String,
    pub destination: String,
    pub status: String, // e.g., "pending", "downloading", "paused", "completed", "failed"
    pub progress: f32,  // Progress percentage (0.0 to 100.0)
}

/// Shared state to store active tasks in memory.
/// In a real system, you'd integrate with your `task_manager` or database logic here.
type AppState = Arc<Mutex<HashMap<String, DownloadTask>>>;

/// Handler: Start a new download task.
async fn start_download(
    data: web::Data<AppState>,
    task: web::Json<DownloadTask>,
) -> Result<impl Responder> {
    let mut state = data.lock().unwrap();
    let task_id = task.id.clone();

    // In a real app, you'd call your `task_manager.add_task(...)` or a function from `download.rs`.
    state.insert(task_id.clone(), task.into_inner());

    Ok(HttpResponse::Ok().json(serde_json::json!({
        "message": "Download started",
        "task_id": task_id,
    })))
}

/// Handler: Retrieve the status of a specific download task.
async fn get_download_status(
    data: web::Data<AppState>,
    task_id: web::Path<String>,
) -> Result<impl Responder> {
    let state = data.lock().unwrap();

    if let Some(task) = state.get(&task_id.into_inner()) {
        Ok(HttpResponse::Ok().json(task))
    } else {
        Ok(HttpResponse::NotFound().json(serde_json::json!({
            "error": "Task not found",
        })))
    }
}

/// Handler: Pause a specific download task.
async fn pause_download(
    data: web::Data<AppState>,
    task_id: web::Path<String>,
) -> Result<impl Responder> {
    let mut state = data.lock().unwrap();

    if let Some(task) = state.get_mut(&task_id.into_inner()) {
        // In a real app, you'd call something like `task_manager.pause_task(...)`.
        task.status = "paused".to_string();
        return Ok(HttpResponse::Ok().json(serde_json::json!({
            "message": "Download paused",
            "task_id": task.id,
        })));
    }

    Ok(HttpResponse::NotFound().json(serde_json::json!({
        "error": "Task not found"
    })))
}

/// Handler: Resume a specific download task.
async fn resume_download(
    data: web::Data<AppState>,
    task_id: web::Path<String>,
) -> Result<impl Responder> {
    let mut state = data.lock().unwrap();

    if let Some(task) = state.get_mut(&task_id.into_inner()) {
        // In a real app, you'd call something like `task_manager.resume_task(...)`.
        task.status = "downloading".to_string();
        return Ok(HttpResponse::Ok().json(serde_json::json!({
            "message": "Download resumed",
            "task_id": task.id,
        })));
    }

    Ok(HttpResponse::NotFound().json(serde_json::json!({
        "error": "Task not found"
    })))
}

/// Handler: Cancel a download task.
async fn cancel_download(
    data: web::Data<AppState>,
    task_id: web::Path<String>,
) -> Result<impl Responder> {
    let mut state = data.lock().unwrap();

    // In a real app, you'd do `task_manager.cancel_task(...)`.
    if state.remove(&task_id.into_inner()).is_some() {
        Ok(HttpResponse::Ok().json(serde_json::json!({
            "message": "Download canceled"
        })))
    } else {
        Ok(HttpResponse::NotFound().json(serde_json::json!({
            "error": "Task not found"
        })))
    }
}

/// Handler: List all current download tasks.
async fn list_downloads(data: web::Data<AppState>) -> Result<impl Responder> {
    let state = data.lock().unwrap();
    let tasks: Vec<&DownloadTask> = state.values().collect();

    Ok(HttpResponse::Ok().json(tasks))
}

/// Configures the routes for our API. You can call this from your main function
/// or from another location to set up the Actix Web app.
pub fn configure_api(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/api")
            .route("/download", web::post().to(start_download))
            .route("/download/{id}", web::get().to(get_download_status))
            .route("/download/{id}/pause", web::post().to(pause_download))
            .route("/download/{id}/resume", web::post().to(resume_download))
            .route("/download/{id}/cancel", web::post().to(cancel_download))
            .route("/downloads", web::get().to(list_downloads)),
    );
}

/// Optional main function if you want to run this API stand-alone. Otherwise,
/// you can integrate `configure_api` into your existing Actix Web server.
#[actix_web::main]
pub async fn run_api_server() -> std::io::Result<()> {
    let state = Arc::new(Mutex::new(HashMap::<String, DownloadTask>::new()));

    HttpServer::new(move || {
        App::new()
            .app_data(web::Data::new(state.clone()))
            .configure(configure_api) // Use the API config
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
}
