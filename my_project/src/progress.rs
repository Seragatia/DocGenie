/// Calculates and returns the download progress as a percentage string (e.g., "45.67%").
/// If `total_size` is zero, it returns "0.00%". The progress is clamped to 100%
/// in case the `downloaded_size` exceeds the `total_size`.
pub fn track_progress(total_size: u64, downloaded_size: u64) -> String {
    if total_size == 0 {
        return "0.00%".to_string();
    }
    // Calculate the raw progress percentage.
    let progress = (downloaded_size as f64 / total_size as f64) * 100.0;
    // Clamp the progress to 100% (in case of slight over-estimates).
    let clamped_progress = progress.min(100.0);
    format!("{:.2}%", clamped_progress)
}
