diesel::table! {
    downloads (id) {
        // Use Text for string IDs.
        id -> Text,
        // The URL of the download.
        url -> Text,
        // The destination where the file is saved.
        destination -> Text,
        // The current status of the download (e.g., pending, downloading, completed, failed).
        status -> Text,
        // The current progress percentage (e.g., 0.0 to 100.0).
        progress -> Float,
        // Optional number of segments for segmented downloads.
        segments -> Nullable<Integer>,
        // Timestamp for when the download record was created.
        created_at -> Timestamp,
    }
}
