fn main() {
    let webui_var = std::env::var("AW_WEBUI_DIR");
    let path = if let Ok(var_path) = &webui_var {
        std::path::PathBuf::from(var_path)
    } else {
        let path = std::path::PathBuf::from("../../build/frontend-artifact");
        std::fs::create_dir_all(&path).expect("failed to create frontend artifact directory");
        println!("cargo:rustc-env=AW_WEBUI_DIR={}", path.display());
        path
    };

    if !path.join("index.html").exists() {
        println!(
            "cargo:warning=`{}` is not built, compiling without webui",
            path.display()
        );
    }

    // Rebuild if the webui directory changes
    println!("cargo:rerun-if-changed={}", path.display());
    println!("cargo:rerun-if-env-changed=AW_WEBUI_DIR");

    tauri_build::build();
}
