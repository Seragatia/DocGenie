// download.rs
use std::error::Error;
use reqwest::blocking::Client;

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_setup_connection() {
        let url = "https://example.com";
        let client = setup_connection(url);
        assert!(client.is_ok());
    }

    #[test]
    fn test_download_file() {
        // Simulate a small file download (using a mock or real URL)
        let url = "https://example.com/small_file.txt";
        let file_path = "test_file.txt";
        let range_start = 0;
        
        let result = download_file(&Client::new(), url, file_path, range_start);
        assert!(result.is_ok());
    }

    #[test]
    fn test_retry_download() {
        // Simulate a retry mechanism when downloading a file
        let url = "https://example.com/small_file.txt";
        let file_path = "test_file.txt";
        let range_start = 0;
        
        let downloader = Downloader::new(5, 2); // max_retries: 5, base_delay: 2 seconds
        let result = downloader.retry_download(url, file_path, range_start);
        assert!(result.is_ok());
    }
}
