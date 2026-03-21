use std::path::PathBuf;

#[cfg(not(target_os = "android"))]
use std::fs;

#[cfg(target_os = "android")]
use std::sync::Mutex;

#[cfg(target_os = "android")]
lazy_static! {
    static ref ANDROID_DATA_DIR: Mutex<PathBuf> = Mutex::new(PathBuf::from(
        "/data/user/0/net.activitywatch.android/files"
    ));
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
fn prepare_scoped_dir(primary_root: PathBuf, legacy_root: PathBuf, scope: &str) -> Result<PathBuf, ()> {
    let mut dir = prefer_runtime_root(primary_root, legacy_root);
    dir.push(scope);
    fs::create_dir_all(dir.clone()).expect("Unable to create runtime dir");
    Ok(dir)
}

#[cfg(not(target_os = "android"))]
pub fn get_config_dir() -> Result<PathBuf, ()> {
    prepare_scoped_dir(
        appdirs::user_config_dir(Some(TRUST_ME_APP_NAME), None, false)?,
        appdirs::user_config_dir(Some(LEGACY_APP_NAME), None, false)?,
        "aw-server-rust",
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
        "aw-server-rust",
    )
}

#[cfg(target_os = "android")]
pub fn get_data_dir() -> Result<PathBuf, ()> {
    return Ok(ANDROID_DATA_DIR.lock().unwrap().to_path_buf());
}

#[cfg(not(target_os = "android"))]
pub fn get_cache_dir() -> Result<PathBuf, ()> {
    prepare_scoped_dir(
        appdirs::user_cache_dir(Some(TRUST_ME_APP_NAME), None)?,
        appdirs::user_cache_dir(Some(LEGACY_APP_NAME), None)?,
        "aw-server-rust",
    )
}

#[cfg(target_os = "android")]
pub fn get_cache_dir() -> Result<PathBuf, ()> {
    panic!("not implemented on Android");
}

#[cfg(not(target_os = "android"))]
pub fn get_log_dir(module: &str) -> Result<PathBuf, ()> {
    prepare_scoped_dir(
        appdirs::user_log_dir(Some(TRUST_ME_APP_NAME), None)?,
        appdirs::user_log_dir(Some(LEGACY_APP_NAME), None)?,
        module,
    )
}

#[cfg(target_os = "android")]
pub fn get_log_dir(module: &str) -> Result<PathBuf, ()> {
    panic!("not implemented on Android");
}

pub fn db_path(testing: bool) -> Result<PathBuf, ()> {
    let mut db_path = get_data_dir()?;
    if testing {
        db_path.push("sqlite-testing.db");
    } else {
        db_path.push("sqlite.db");
    }
    Ok(db_path)
}

#[cfg(target_os = "android")]
pub fn set_android_data_dir(path: &str) {
    let mut android_data_dir = ANDROID_DATA_DIR.lock().unwrap();
    *android_data_dir = PathBuf::from(path);
}

#[test]
fn test_get_dirs() {
    #[cfg(target_os = "android")]
    set_android_data_dir("/test");

    get_cache_dir().unwrap();
    get_log_dir("aw-server-rust").unwrap();
    db_path(true).unwrap();
    db_path(false).unwrap();
}
