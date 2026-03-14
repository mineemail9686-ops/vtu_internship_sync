import argparse
from sync_engine import run_sync
from config import logger

def main():
    parser = argparse.ArgumentParser(description="VTU Internship Portal Diary Sync Tool")
    parser.add_argument('--sync', action='store_true', help="Run the full synchronization (Account-2 -> Account-1)")
    parser.add_argument('--dry-run', action='store_true', help="Scrape and diff data, print results, but do not submit to Account-1")
    parser.add_argument('--headless', action='store_true', help="Run Chrome browser in background (headless) mode")
    parser.add_argument('--resume', action='store_true', help="Only attempt to sync dates previously logged as failed in checkpoint.json")

    args = parser.parse_args()

    # If no functional flags are supplied, default to showing help
    if not any([args.sync, args.dry_run, args.resume]):
        parser.print_help()
        return

    logger.info("Initializing VTU Sync CLI")
    
    if args.dry_run:
        logger.info("Starting DRY RUN sync")
        run_sync(headless=args.headless, dry_run=True, resume=args.resume)
        
    elif args.sync or args.resume:
        mode_str = "RESUMING FAILED SYNC" if args.resume else "FULL SYNC"
        logger.info(f"Starting {mode_str}")
        run_sync(headless=args.headless, dry_run=False, resume=args.resume)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\nExecution interrupted by user.")
    except Exception as e:
        logger.critical(f"Fatal error during execution: {e}", exc_info=True)
