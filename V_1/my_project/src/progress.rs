use std::time::{Duration, Instant};

pub struct ProgressTracker {
    total_bytes: u64,
    downloaded_bytes: u64,
    start_time: Instant,
    last_update: Instant,
    last_downloaded_bytes: u64,
}

impl ProgressTracker {
    // Initialize a new ProgressTracker with the total file size
    pub fn new(total_bytes: u64) -> Self {
        ProgressTracker {
            total_bytes,
            downloaded_bytes: 0,
            start_time: Instant::now(),
            last_update: Instant::now(),
            last_downloaded_bytes: 0,
        }
    }

    // Update the progress tracker with new bytes downloaded
    pub fn update(&mut self, new_bytes: u64) {
        self.downloaded_bytes += new_bytes;
        self.last_update = Instant::now();
        self.last_downloaded_bytes = new_bytes;
    }

    // Calculate and return the percentage of the file that has been downloaded
    pub fn percentage(&self) -> f64 {
        if self.total_bytes == 0 {
            0.0
        } else {
            (self.downloaded_bytes as f64 / self.total_bytes as f64) * 100.0
        }
    }

    // Calculate and return the current download speed (bytes per second)
    pub fn transfer_rate(&self) -> f64 {
        let elapsed_time = self.last_update.duration_since(self.start_time).as_secs_f64();
        if elapsed_time == 0.0 {
            return 0.0;
        }
        self.last_downloaded_bytes as f64 / elapsed_time
    }

    // Calculate and return the estimated time remaining for the download
    pub fn eta(&self) -> Option<Duration> {
        if self.downloaded_bytes == 0 || self.transfer_rate() == 0.0 {
            return None;
        }

        let remaining_bytes = self.total_bytes.saturating_sub(self.downloaded_bytes);
        let remaining_time = remaining_bytes as f64 / self.transfer_rate();
        Some(Duration::from_secs_f64(remaining_time))
    }
}

