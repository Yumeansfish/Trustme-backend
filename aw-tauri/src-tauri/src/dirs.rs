//! Directory management for the Trust-me Tauri shell
//!
//! Supported platforms: Windows, Linux, macOS, Android

use std::fs;
use std::path::PathBuf;

#[cfg(target_os = "android")]
use std::sync::Mutex;

#[cfg(target_os = "android")]
use lazy_static::lazy_static;

#[cfg(target_os = "android")]
lazy_static! {
    static ref ANDROID_DATA_DIR: Mutex<PathBuf> =
        Mutex::new(PathBuf::from("/data/user/0/net.activitywatch.app/files"));
}

#[cfg(not(target_os = "android"))]
const TRUST_ME_APP_NAME: &str = "trust-me";
#[cfg(not(target_os = "android"))]
const LEGACY_APP_NAME: &str = "activitywatch";

#[cfg(not(target_os = "android"))]
fn prefer_runtime_root(primary: PathBuf, legacy: PathBuf) -> PathBuf {
    if primary.exists() {
        primary
    } else if legacy.exists() {
        legacy
    } else {
        primary
    }
}

#[cfg(not(target_os = "android"))]
fn prepare_scoped_dir(
    primary_root: PathBuf,
    legacy_root: PathBuf,
    components: &[&str],
) -> Result<PathBuf, ()> {
    let mut dir = prefer_runtime_root(primary_root, legacy_root);
    for component in components {
        dir.push(component);
    }
    fs::create_dir_all(dir.clone()).expect("Unable to create runtime dir");
    Ok(dir)
}

#[cfg(not(target_os = "android"))]
pub fn get_config_dir() -> Result<PathBuf, ()> {
    prepare_scoped_dir(
        appdirs::user_config_dir(Some(TRUST_ME_APP_NAME), None, false)?,
        appdirs::user_config_dir(Some(LEGACY_APP_NAME), None, false)?,
        &["aw-tauri"],
    )
}

#[cfg(target_os = "android")]
pub fn get_config_dir() -> Result<PathBuf, ()> {
    panic!("not implemented on Android");
}

#[cfg(not(target_os = "android"))]
pub fn get_data_dir() -> Result<PathBuf, ()> {
    prepare_scoped_dir(
        appdirs::user_data_dir(Some(TRUST_ME_APP_NAME), None, false)?,
        appdirs::user_data_dir(Some(LEGACY_APP_NAME), None, false)?,
        &["aw-tauri"],
    )
}

#[cfg(target_os = "android")]
pub fn get_data_dir() -> Result<PathBuf, ()> {
    Ok(ANDROID_DATA_DIR
        .lock()
        .expect("Unable to create data dir")
        .to_path_buf())
}

#[cfg(all(not(target_os = "android"), target_os = "linux"))]
pub fn get_log_dir() -> Result<PathBuf, ()> {
    // Linux uses cache dir for logs
    prepare_scoped_dir(
        appdirs::user_cache_dir(Some(TRUST_ME_APP_NAME), None)?,
        appdirs::user_cache_dir(Some(LEGACY_APP_NAME), None)?,
        &["aw-tauri", "log"],
    )
}

#[cfg(all(not(target_os = "android"), not(target_os = "linux")))]
pub fn get_log_dir() -> Result<PathBuf, ()> {
    // Windows and macOS use dedicated log directories
    prepare_scoped_dir(
        appdirs::user_log_dir(Some(TRUST_ME_APP_NAME), None)?,
        appdirs::user_log_dir(Some(LEGACY_APP_NAME), None)?,
        &["aw-tauri"],
    )
}

#[cfg(target_os = "android")]
pub fn get_log_dir() -> Result<PathBuf, ()> {
    panic!("not implemented on Android");
}

pub fn get_config_path() -> PathBuf {
    let mut path = get_config_dir().expect("Failed to get config dir");
    path.push("config.toml");
    path
}

pub fn get_log_path() -> PathBuf {
    let mut path = get_log_dir().expect("Failed to get log dir");
    path.push("aw-tauri.log");
    path
}

#[cfg(target_os = "linux")]
pub fn get_runtime_dir() -> PathBuf {
    // Linux: use XDG_RUNTIME_DIR or fallback to cache dir
    if let Ok(runtime_dir) = std::env::var("XDG_RUNTIME_DIR") {
        let primary = PathBuf::from(&runtime_dir).join(TRUST_ME_APP_NAME);
        let legacy = PathBuf::from(&runtime_dir).join(LEGACY_APP_NAME);
        let mut dir = prefer_runtime_root(primary, legacy);
        dir.push("aw-tauri");
        if fs::create_dir_all(dir.clone()).is_ok() {
            return dir;
        }
    }
    // Fallback to cache dir
    let primary_root =
        appdirs::user_cache_dir(Some(TRUST_ME_APP_NAME), None).unwrap_or_else(|_| {
            PathBuf::from("/tmp").join(TRUST_ME_APP_NAME)
        });
    let legacy_root = appdirs::user_cache_dir(Some(LEGACY_APP_NAME), None)
        .unwrap_or_else(|_| PathBuf::from("/tmp").join(LEGACY_APP_NAME));
    let mut dir = prefer_runtime_root(primary_root, legacy_root);
    dir.push("aw-tauri");
    let _ = fs::create_dir_all(dir.clone());
    dir
}

#[cfg(any(target_os = "windows", target_os = "macos"))]
pub fn get_runtime_dir() -> PathBuf {
    // For Windows and macOS, use data directory for runtime files
    get_data_dir().unwrap_or_else(|_| PathBuf::from("."))
}

#[cfg(target_os = "android")]
pub fn get_runtime_dir() -> PathBuf {
    get_data_dir().unwrap_or_else(|_| PathBuf::from("/tmp"))
}

pub fn get_discovery_paths() -> Vec<PathBuf> {
    let mut discovery_paths = Vec::new();

    #[cfg(target_os = "linux")]
    {
        // Linux: XDG-compliant paths
        if let Ok(home_dir) = std::env::var("HOME") {
            let home_path = PathBuf::from(&home_dir);

            // User executables directories
            discovery_paths.push(home_path.join("bin")); // ~/bin (traditional)
            discovery_paths.push(home_path.join(".local").join("bin")); // ~/.local/bin (modern XDG)

            // XDG_DATA_HOME or ~/.local/share (user data)
            let data_dir = std::env::var("XDG_DATA_HOME")
                .map(PathBuf::from)
                .unwrap_or_else(|_| home_path.join(".local").join("share"));
            discovery_paths.push(
                data_dir
                    .join("trust-me")
                    .join("aw-tauri")
                    .join("modules"),
            );
            discovery_paths.push(
                data_dir
                    .join("activitywatch")
                    .join("aw-tauri")
                    .join("modules"),
            );

            // Legacy paths for backward compatibility
            discovery_paths.push(home_path.join("aw-modules"));
        }
    }

    #[cfg(target_os = "windows")]
    {
        // Windows: User-specific and system paths
        if let Ok(username) = std::env::var("USERNAME") {
            discovery_paths.push(PathBuf::from(format!(r"C:/Users/{}/aw-modules", username)));
            discovery_paths.push(PathBuf::from(format!(
                r"C:/Users/{}/AppData/Local/Programs/Trust-me",
                username
            )));
            discovery_paths.push(PathBuf::from(format!(
                r"C:/Users/{}/AppData/Local/Programs/ActivityWatch",
                username
            )));
        }
    }

    #[cfg(target_os = "macos")]
    {
        // macOS: Application bundle and user paths
        if let Ok(home_dir) = std::env::var("HOME") {
            discovery_paths.push(PathBuf::from(home_dir).join("aw-modules"));
        }
        discovery_paths.push(PathBuf::from(
            "/Applications/Trust-me.app/Contents/MacOS",
        ));
        discovery_paths.push(PathBuf::from(
            "/Applications/Trust-me.app/Contents/Resources",
        ));
        discovery_paths.push(PathBuf::from(
            "/Applications/ActivityWatch.app/Contents/MacOS",
        ));
        discovery_paths.push(PathBuf::from(
            "/Applications/ActivityWatch.app/Contents/Resources",
        ));
    }

    #[cfg(target_os = "android")]
    {
        // Android: No discovery paths needed for mobile platform
    }

    discovery_paths
}

#[cfg(target_os = "android")]
pub fn set_android_data_dir(path: &str) {
    let mut android_data_dir = ANDROID_DATA_DIR
        .lock()
        .expect("Unable to acquire ANDROID_DATA_DIR lock");
    *android_data_dir = PathBuf::from(path);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_get_dirs() {
        #[cfg(target_os = "android")]
        set_android_data_dir("/test");

        #[cfg(not(target_os = "android"))]
        {
            get_config_dir().expect("Failed to get config directory");
            get_log_dir().expect("Failed to get log directory");
        }

        get_data_dir().expect("Failed to get data directory");

        let _ = get_config_path();
        let _ = get_log_path();
        let _ = get_runtime_dir();
        let _ = get_discovery_paths();
    }

    #[test]
    fn test_paths_exist() {
        #[cfg(target_os = "android")]
        set_android_data_dir("/test");

        #[cfg(not(target_os = "android"))]
        {
            let config_path = get_config_path();
            let log_path = get_log_path();

            // The parent directories should exist after calling the functions
            assert!(config_path.parent().unwrap().exists());
            assert!(log_path.parent().unwrap().exists());
        }
    }
}
