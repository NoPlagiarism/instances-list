try:
    from .generate_md_json import run as gen_run
    from .main import run as main_run
except ImportError:
    from generate_md_json import run as gen_run
    from main import run as main_run

if __name__ == "__main__":
    main_run()
    gen_run()
