use dirs::home_dir;
use std::error::Error;
use std::fs;
use std::path::PathBuf;

const TRUST_ME_CONFIG_ROOT: &str = "trust-me";
const LEGACY_CONFIG_ROOT: &str = "activitywatch";
const TRUST_ME_SYNC_ROOT: &str = "TrustMeSync";
const LEGACY_SYNC_ROOT: &str = "ActivityWatchSync";

fn prefer_root(primary: PathBuf, legacy: PathBuf) -> PathBuf {
    if primary.exists() {
        primary
    } else if legacy.exists() {
        legacy
    } else {
        primary
    }
}

// TODO: This could be refactored to share logic with aw-server/src/dirs.rs
// TODO: add proper config support
#[allow(dead_code)]
pub fn get_config_dir() -> Result<PathBuf, Box<dyn Error>> {
    let primary = appdirs::user_config_dir(Some(TRUST_ME_CONFIG_ROOT), None, false)
        .map_err(|_| "Unable to read user config dir")?;
    let legacy = appdirs::user_config_dir(Some(LEGACY_CONFIG_ROOT), None, false)
        .map_err(|_| "Unable to read user config dir")?;
    let mut dir = prefer_root(primary, legacy);
    dir.push("aw-sync");
    fs::create_dir_all(dir.clone())?;
    Ok(dir)
}

pub fn get_server_config_path(testing: bool) -> Result<PathBuf, ()> {
    let dir = aw_server::dirs::get_config_dir()?;
    Ok(dir.join(if testing {
        "config-testing.toml"
    } else {
        "config.toml"
    }))
}

pub fn get_sync_dir() -> Result<PathBuf, Box<dyn Error>> {
    // if AW_SYNC_DIR is set, use that
    if let Ok(dir) = std::env::var("AW_SYNC_DIR") {
        return Ok(PathBuf::from(dir));
    }
    let home_dir = home_dir().ok_or("Unable to read home_dir")?;
    Ok(prefer_root(
        home_dir.join(TRUST_ME_SYNC_ROOT),
        home_dir.join(LEGACY_SYNC_ROOT),
    ))
}
