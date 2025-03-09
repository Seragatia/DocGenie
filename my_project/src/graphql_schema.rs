// src/graphql_schema.rs

use async_graphql::{Object, Schema, Result as GQLResult, Error as GQLError, EmptySubscription};
use my_project::download::retry_download;
use tokio::task;
use log::debug;

/// The Query root provides a simple health check.
pub struct QueryRoot;

#[Object]
impl QueryRoot {
    async fn health(&self) -> &str {
        "Backend is running"
    }
}

/// The Mutation root provides a mutation to start a download.
/// The `start_download` mutation accepts a URL and spawns a blocking task to perform the download.
/// If the download task fails or the task join fails, an error is returned.
pub struct MutationRoot;

#[Object]
impl MutationRoot {
    async fn start_download(&self, url: String) -> GQLResult<&str> {
        // Spawn a blocking task to run the download.
        // Here, we use a default download path ("default_download_path") and a progress callback that logs progress.
        let result = task::spawn_blocking(move || {
            retry_download(
                &url,
                "default_download_path", // You might replace this with a proper destination path.
                5,
                |downloaded_bytes, total_bytes| {
                    debug!("Download progress: {} / {} bytes", downloaded_bytes, total_bytes);
                },
            )
        })
        .await
        .map_err(|e| GQLError::new(format!("Task join error: {}", e)))?;
        
        result.map_err(|e| GQLError::new(format!("Download error: {}", e)))?;
        Ok("Download started successfully")
    }
}

/// Type alias for the GraphQL Schema.
pub type AppSchema = Schema<QueryRoot, MutationRoot, EmptySubscription>;

/// Builds and returns the GraphQL schema.
pub fn build_schema() -> AppSchema {
    Schema::build(QueryRoot, MutationRoot, EmptySubscription).finish()
}
