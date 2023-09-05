from lib.website_comparer import WebsiteComparer
import time

def elapsed_time_from(start_time):
    elapsed_time = time.time() - start_time
    hours = int(elapsed_time // 3600)
    minutes = int((elapsed_time % 3600) // 60)
    seconds = int(elapsed_time % 60)
    return [hours, minutes, seconds]

def select_type():
    print("Type compare:")
    print("  1. Single page")
    print("  2. Multiple pages")
    print("  3. Cancel compare")
    compare_type = input("Enter type: ")
    if compare_type not in ['1', '2']:
        return [compare_type, None]

    path = input("Enter the path: ")
    return [compare_type, path]

if __name__ == "__main__":
    domain1 = "https://kuruma-mb5.zigexn.vn/usedcar"
    domain2 = "https://kuruma-mb8.zigexn.vn/usedcar"
    csv_name = input("Type csv name: ")
    comparer = WebsiteComparer(domain1, domain2, csv_name=csv_name)
    
    compare_type, path = select_type()
    start_time = time.time()
    while True:
        match compare_type:
            case '1':
                comparer.compare_single_page(path)
                break
            case '2':
                comparer.compare_multiple_pages(path)
                break
            case '3':
                break
            case _:
                print("Invalid type. Please select again")
                compare_type, path = select_type()

    # Close browsers
    comparer.driver1.quit()
    comparer.driver2.quit()
    h, m, s = elapsed_time_from(start_time)
    print(f"Elapsed time: {h} giờ {m} phút {s} giây")
    # print("Start save all path: ")
    # comparer.save_page_urls("filter pages", comparer.filter_paths, f"{csv_name}_filter_paths.txt")
    # print("Start save checked path")
    # comparer.save_page_urls("checked_page", comparer.checked_paths, f"{csv_name}_checked_paths.txt")
    # print("Start save ignore paths...")
    # comparer.save_page_urls("ignore_page", comparer.ignore_paths, f"{csv_name}_ignore_paths.txt")
    print("Goodbye!!!")
