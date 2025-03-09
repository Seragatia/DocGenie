//! Main entry point for the Rust backend server using Actix Web.
//! This server manages download tasks and applies Diesel migrations (if enabled).
//! Logging is configured using Simplelog.

use actix_web::{App, HttpServer};
use my_project::api::api::{configure_api, health_check, DownloadTask};
use my_project::api::metadata::configure_metadata;
use std::{
    collections::HashMap,
    sync::{Arc, RwLock},
    env,
};
use actix_web::web::Data;
use log::info;
use tokio::signal;

use simplelog::{
    CombinedLogger, WriteLogger, TermLogger, TerminalMode, ColorChoice,
    ConfigBuilder, LevelFilter, SharedLogger,
};
use std::fs::File;

#[cfg(feature = "with-diesel")]
use diesel::{prelude::*, sqlite::SqliteConnection};

#[cfg(feature = "with-diesel")]
use diesel_migrations::{embed_migrations, EmbeddedMigrations, MigrationHarness};

#[cfg(feature = "with-diesel")]
pub const MIGRATIONS: EmbeddedMigrations = embed_migrations!("./migrations");

type AppState = Arc<RwLock<HashMap<String, DownloadTask>>>;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    setup_logging()?;
    info!("Starting Rust backend server...");

    #[cfg(feature = "with-diesel")]
    if let Err(e) = run_migrations() {
        log::error!("Failed to run migrations: {}", e);
    }

    let state: AppState = Arc::new(RwLock::new(HashMap::new()));
    let port = env::var("SERVER_PORT").unwrap_or_else(|_| "8080".to_string());
    let address = format!("127.0.0.1:{}", port);

    let server = HttpServer::new(move || {
        App::new()
            .app_data(Data::new(state.clone()))
            .service(health_check)
            .configure(configure_api)
            .configure(configure_metadata)
    })
    .bind(&address)?
    .run();

    info!("Server running at http://{}", address);
    tokio::select! {
        res = server => { res?; }
        _ = signal::ctrl_c() => {
            info!("Received shutdown signal, stopping server...");
        }
    }
    Ok(())
}

fn setup_logging() -> Result<(), std::io::Error> {
    let log_file = File::create("rust_backend.log")?;
    let log_config = ConfigBuilder::new().build();
    let term_logger: Box<dyn SharedLogger> = TermLogger::new(
        LevelFilter::Info, log_config.clone(), TerminalMode::Mixed, ColorChoice::Auto,
    );

    CombinedLogger::init(vec![
        WriteLogger::new(LevelFilter::Debug, log_config, log_file),
        term_logger,
    ])
    .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e.to_string()))
}

#[cfg(feature = "with-diesel")]
fn run_migrations() -> Result<(), Box<dyn std::error::Error>> {
    let database_url = env::var("DATABASE_URL")?;
    let mut conn = SqliteConnection::establish(&database_url)?;
    conn.run_pending_migrations(MIGRATIONS)?;
    info!("✅ Diesel migrations applied successfully.");
    Ok(())
}
