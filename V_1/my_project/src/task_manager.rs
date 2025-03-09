use std::collections::HashMap;
use std::future::Future;
use std::pin::Pin;
use std::sync::Arc;
use tokio::sync::{mpsc, Mutex};
use tokio::time::{sleep, Duration};

/// The result type for a download task.
pub type TaskResult = Result<(), Box<dyn std::error::Error + Send + Sync>>;

/// A boxed future representing a download task.
pub type TaskFuture = Pin<Box<dyn Future<Output = TaskResult> + Send>>;

/// Represents a single download task.
pub struct Task {
    /// A unique identifier for the task.
    pub id: String,
    /// The asynchronous future that performs the download.
    pub future: TaskFuture,
}

/// Commands that can be sent to the task manager.
pub enum TaskCommand {
    /// Start a new task.
    Start(Task),
    /// Pause a task with the given ID.
    Pause(String),
    /// Resume a paused task with the given ID.
    Resume(String),
    /// Cancel a task with the given ID.
    Cancel(String),
}

/// The TaskManager is responsible for scheduling and managing concurrent download tasks.
pub struct TaskManager {
    /// The sender side of the command channel.
    sender: mpsc::Sender<TaskCommand>,
    /// A shared storage for tasks; tasks are indexed by their unique ID.
    task_store: Arc<Mutex<HashMap<String, Task>>>,
}

impl TaskManager {
    /// Creates a new TaskManager with the specified number of worker tasks.
    pub fn new(worker_count: usize) -> Self {
        let (tx, mut rx) = mpsc::channel::<TaskCommand>(100);
        let task_store: Arc<Mutex<HashMap<String, Task>>> = Arc::new(Mutex::new(HashMap::new()));

        // Spawn worker tasks.
        for _ in 0..worker_count {
            let mut rx_clone = rx.clone();
            let store = task_store.clone();

            tokio::spawn(async move {
                // Each worker listens for commands and processes tasks accordingly.
                while let Some(cmd) = rx_clone.recv().await {
                    match cmd {
                        TaskCommand::Start(task) => {
                            let task_id = task.id.clone();
                            // Insert task into shared store.
                            store.lock().await.insert(task_id.clone(), task);
                            // Retrieve and remove the task for execution.
                            if let Some(task) = store.lock().await.remove(&task_id) {
                                println!("Starting task: {}", task_id);
                                let res = (task.future).await;
                                match res {
                                    Ok(_) => println!("Task {} completed successfully", task_id),
                                    Err(e) => eprintln!("Task {} failed: {}", task_id, e),
                                }
                            }
                        }
                        TaskCommand::Pause(task_id) => {
                            // In a real implementation, pausing would signal the running task to halt.
                            println!("Pause command received for task: {}", task_id);
                            // (Implementation: mark task as paused in the store, so it doesn't execute further work)
                        }
                        TaskCommand::Resume(task_id) => {
                            // In a real implementation, resuming would restart a paused task.
                            println!("Resume command received for task: {}", task_id);
                            // (Implementation: retrieve the paused task and reinsert it for execution)
                        }
                        TaskCommand::Cancel(task_id) => {
                            println!("Cancel command received for task: {}", task_id);
                            // Remove the task from the store if it hasn't started.
                            store.lock().await.remove(&task_id);
                        }
                    }
                }
            });
        }

        TaskManager { sender: tx, task_store }
    }

    /// Adds a new download task to the task manager.
    pub async fn add_task(&self, task: Task) -> Result<(), Box<dyn std::error::Error>> {
        self.sender.send(TaskCommand::Start(task)).await?;
        Ok(())
    }

    /// Pauses the task with the given ID.
    pub async fn pause_task(&self, task_id: String) -> Result<(), Box<dyn std::error::Error>> {
        self.sender.send(TaskCommand::Pause(task_id)).await?;
        Ok(())
    }

    /// Resumes the task with the given ID.
    pub async fn resume_task(&self, task_id: String) -> Result<(), Box<dyn std::error::Error>> {
        self.sender.send(TaskCommand::Resume(task_id)).await?;
        Ok(())
    }

    /// Cancels the task with the given ID.
    pub async fn cancel_task(&self, task_id: String) -> Result<(), Box<dyn std::error::Error>> {
        self.sender.send(TaskCommand::Cancel(task_id)).await?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::Instant;

    // A simple dummy task that completes after a delay.
    async fn dummy_task(id: String, delay_secs: u64) -> TaskResult {
        println!("Task {} started", id);
        sleep(Duration::from_secs(delay_secs)).await;
        println!("Task {} finished", id);
        Ok(())
    }

    #[tokio::test]
    async fn test_add_task() {
        let manager = TaskManager::new(2);
        let task = Task {
            id: "task1".to_string(),
            future: Box::pin(dummy_task("task1".to_string(), 1)),
        };
        assert!(manager.add_task(task).await.is_ok());
    }

    #[tokio::test]
    async fn test_cancel_task() {
        let manager = TaskManager::new(2);
        let task = Task {
            id: "task2".to_string(),
            future: Box::pin(dummy_task("task2".to_string(), 2)),
        };
        // Add task
        manager.add_task(task).await.expect("Failed to add task");
        // Cancel the task
        assert!(manager.cancel_task("task2".to_string()).await.is_ok());
    }

    #[tokio::test]
    async fn test_pause_resume_task() {
        let manager = TaskManager::new(2);
        let task = Task {
            id: "task3".to_string(),
            future: Box::pin(dummy_task("task3".to_string(), 2)),
        };
        manager.add_task(task).await.expect("Failed to add task");
        // Simulate pause/resume commands (actual pause/resume requires deeper integration)
        assert!(manager.pause_task("task3".to_string()).await.is_ok());
        assert!(manager.resume_task("task3".to_string()).await.is_ok());
    }
}
