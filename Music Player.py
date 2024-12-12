import os, subprocess, sys, re, json
from pathlib import Path
from time import sleep

from colorama import Fore, Style, init

init()

HEADER = Fore.MAGENTA  
INFO = Fore.BLUE       
SUCCESS = Fore.CYAN    
PROMPT = Fore.LIGHTMAGENTA_EX  
ERROR = Fore.RED       
RESET = Style.RESET_ALL

def get_script_directory():
    if getattr(sys, 'frozen', False):  
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def resolve_path(file_name):
    return os.path.join(get_script_directory(), file_name)

def read_file(file_path, default_value=100):
    if not os.path.exists(file_path):
        write_file(file_path, default_value)  
        sys.stdout.write(f"{SUCCESS}[file created]: {file_path} with default value: {default_value}{RESET}\n")
    try:
        with open(file_path, "r") as file:
            return file.read().strip()
    except Exception as e:
        sys.stdout.write(f"{ERROR}[error]: could not read file: {e}{RESET}\n")
        return default_value

def write_file(file_path, content):
    try:
        with open(file_path, "w") as file:
            file.write(str(content))
    except Exception as e:
        sys.stdout.write(f"{ERROR}[error]: could not write to file: {e}{RESET}\n")

def read_urls(file_path):
    default_value = """https://www.youtube.com/watch?v=qnStVGoIgBA 24/7 Chillwave FM | Retro vibes, chill synths for relaxed evenings and nostalgic moods
https://www.youtube.com/watch?v=3U6exJIeGw4 24/7 Synthwave FM // Saw waves, Neon lights, Retro vibes and grids everywhere
https://www.youtube.com/watch?v=hiGzdab8bsE 24/7 Vaporwave FM | Windows 95, Michelangelo and Liminal spaces: this is Vaporwave!
https://www.youtube.com/watch?v=WNsOxG0AqjA Nostalgic Gamers Only: 24/7 Chillwave & Retro Games Combo
https://www.youtube.com/watch?v=uYfxDF_QR94 Nightride FM - 24/7 Synthwave Radio
https://www.youtube.com/watch?v=UedTcufyrHc ChillSynth FM - lofi synthwave radio for retro dreaming
https://www.youtube.com/watch?v=Y9q6RYg2Pdg Datawave FM - midfi synthwave radio for retro computer funk
https://www.youtube.com/watch?v=5-anTj1QrWs Spacesynth FM - space disco radio for galactic exploration
https://www.youtube.com/watch?v=MGJWPha7rJw Darksynth FM - dark synthwave radio for action gaming
https://www.youtube.com/watch?v=1PkJmurhQfU EBSM Radio - dark industrial music for cyberpunk clubbing
"""
    if not os.path.exists(file_path):
        write_file(file_path, default_value)
        sys.stdout.write(f"{SUCCESS}[file created]: {file_path} with default tracks{RESET}\n")
        return [(url, title) for url, title in [line.split(maxsplit=1) for line in default_value.strip().split("\n")]]
    
    try:
        with open(file_path, "r") as file:
            lines = file.readlines()
            urls = []
            for line in lines:
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    urls.append((parts[0], parts[1]))
                else:
                    urls.append((parts[0], "unknown title"))
            return urls
    except FileNotFoundError:
        sys.stdout.write(f"{ERROR}[missing]: {file_path} not found{RESET}\n")
        return [(url, "unknown title") for url in default_value.split("\n")]

def display_urls_with_titles(urls):
    os.system('cls')
    sys.stdout.write(f"{HEADER}~ tracks loaded ~{RESET}\n")
    for i, (url) in enumerate(zip(urls), start=1):
        sys.stdout.write(f"{INFO}{i}: {url[0][1]} ({url[0][0]}){RESET}\n")

def get_track_url(playlist_url, track_number):
    try:
        command = ["yt-dlp", "--flat-playlist", "--dump-single-json", playlist_url]
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            playlist_data = json.loads(result.stdout)
            entries = playlist_data.get("entries", [])

            if 1 <= track_number <= len(entries):
                return entries[track_number - 1]["url"]
            else:
                sys.stdout.write(f"{ERROR}[error]: track number {track_number} is out of range{RESET}\n")
                return None
        else:
            sys.stdout.write(f"{ERROR}[error]: failed to fetch playlist data{RESET}\n")
            return None
    except FileNotFoundError:
        sys.stdout.write(f"{ERROR}[missing]: yt-dlp is not installed or in your PATH{RESET}\n")
        return None
    except json.JSONDecodeError:
        sys.stdout.write(f"{ERROR}[error]: failed to parse playlist JSON{RESET}\n")
        return None
    except Exception as e:
        sys.stdout.write(f"{ERROR}[error]: unexpected error occurred: {e}{RESET}\n")
        return None

def play_youtube_audio(url, volume):
    command = [
        "yt-dlp",
        "-f", "bestaudio",
        "-o", "-",  
        url
    ]
    ffplay_command = [
        "ffplay", "-i", "-", 
        "-nodisp", "-autoexit", 
        "-af", f"volume={int(volume)/100}", 
        "-loglevel", "quiet"  
    ]

    try:
        sys.stdout.write(f"{SUCCESS}[playing]: streaming audio at {volume}% volume{RESET}\n")
        with subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.DEVNULL  
        ) as yt_process:
            subprocess.run(
                ffplay_command, 
                stdin=yt_process.stdout, 
                stdout=subprocess.DEVNULL,  
                stderr=subprocess.DEVNULL   
            )
    except FileNotFoundError:
        sys.stdout.write(f"{ERROR}[error]: ensure yt-dlp and ffmpeg are installed and in your PATH{RESET}\n")
    except KeyboardInterrupt:
        sys.stdout.write(f"{ERROR}[stopped]: playback interrupted{RESET}\n")

def is_playlist(url):
    command_check = ["yt-dlp", "--flat-playlist", "--dump-single-json", url]
    result_check = subprocess.run(command_check, capture_output=True, text=True)
    return result_check

def fetch_video_titles(urls):
    titles = []
    for url in urls:
        try:  
            result_check = is_playlist(url)          
            if result_check.returncode == 0:
                metadata = json.loads(result_check.stdout)
                if "entries" in metadata:
                    playlist_title = metadata.get("title", "unknown playlist title")
                    titles.append("[playlist] " + playlist_title)
                else:
                    command_video = ["yt-dlp", "--get-title", url]
                    result_video = subprocess.run(command_video, capture_output=True, text=True)
                    if result_video.returncode == 0:
                        titles.append(result_video.stdout.strip())
                    else:
                        titles.append("unknown title")
            else:
                titles.append("unknown title")
        except FileNotFoundError:
            sys.stdout.write("[error][missing]: yt-dlp is not installed or in your PATH\n")
            titles.append("unknown title")
        except json.JSONDecodeError:
            sys.stdout.write("[error]: Failed to parse JSON metadata\n")
            titles.append("unknown title")
    return titles

def list_video_titles(url, playlist_title):
    sys.stdout.write(f"{INFO}fetching titles...{RESET}\n")
    try:
        command_video = ["yt-dlp", "--get-title", url]
        result_video = subprocess.run(command_video, capture_output=True, text=True)
        if result_video.returncode == 0:
            sys.stdout.write(f"{INFO}{playlist_title}:\n{result_video.stdout.strip()}{RESET}\n")
        else:
            sys.stdout.write("unknown title")
    except FileNotFoundError:
            sys.stdout.write("[error][missing]: yt-dlp is not installed or in your PATH\n")

def clean_title(title):
    return re.sub(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}', '', title).strip()

def add_url(file_path, urls):
    for url in urls:
        if not url:
            sys.stdout.write(f"{ERROR}[error]: no URL provided{RESET}\n")
            continue
        with open(file_path, 'r') as file:
            if url in file.read():
                sys.stdout.write(f"{ERROR}[error]: duplicate url{RESET}\n")
                continue
            
        print(f"{INFO}[loading]: adding {url} to list{RESET}")
        title = fetch_video_titles([url])[0]

        if title == "unknown title":
            reprint_entries(file_path)
            sys.stdout.write(f"{ERROR}[error]: could not fetch title for the URL: {url}{RESET}\n")
            sleep(1.0)
            continue
        
        print(url, title)
        with open(file_path, "a") as file:
            file.write(f"{url} {clean_title(title)}\n")
        reprint_entries(file_path)
        sys.stdout.write(f"{SUCCESS}[added]: {url} ({title}){RESET}\n")

def remove_url(file_path, entry_numbers):
    entry_numbers.sort(reverse=True)
    for entry_number in entry_numbers:
        try:
            entry_number = int(entry_number)
            with open(file_path, 'r') as file:
                lines = file.readlines()
            
            if entry_number < 1 or entry_number > len(lines):
                sys.stdout.write(f"{ERROR}[error]: invalid entry number{RESET}\n")
                return
            lines.pop(entry_number - 1)
            with open(file_path, 'w') as file:
                file.writelines(lines)

        except ValueError:
            sys.stdout.write(f"{ERROR}[error]: invalid number format{RESET}\n")
            return
        except FileNotFoundError:
            sys.stdout.write(f"{ERROR}[error]: file not found{RESET}\n")
            return
        except Exception as e:
            sys.stdout.write(f"{ERROR}[error]: {str(e)}{RESET}\n")
            return
        
        reprint_entries(file_path)
        sys.stdout.write(f"{SUCCESS}[removed]: track {entry_number}{RESET}\n")

def reprint_entries(file_path):
    urls = read_urls(file_path)
    display_urls_with_titles(urls)
    if not urls: sys.stdout.write(f"{HEADER}~ no tracks found ~{RESET}\n")
    
def download_url(url):
    music_folder = Path.home() / "Music"
    downloads_folder = music_folder / "downloads"
    downloads_folder.mkdir(parents=True, exist_ok=True)

    download_title = fetch_video_titles([url])[0]

    if download_title.startswith("[playlist]"):
        playlist_folder = downloads_folder / download_title
        playlist_folder.mkdir(parents=True, exist_ok=True)
        output_template = str(playlist_folder / "%(title)s.%(ext)s")
    else:
        output_template = str(downloads_folder / "%(title)s.%(ext)s")

    command = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--output", output_template,
        url
    ]

    try:
        print(f"{INFO}[downloading]: {url}{RESET}\n")
        
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        sys.stdout.write(f"{SUCCESS}[completed]: download saved to {downloads_folder}{RESET}\n")
    except subprocess.CalledProcessError as e:
        sys.stdout.write(f"{ERROR}[error]: yt-dlp failed with error code {e.returncode}{RESET}\n")
    except FileNotFoundError:
        sys.stdout.write(f"{ERROR}[missing]: yt-dlp is not installed or in your PATH{RESET}\n")
    except Exception as e:
        sys.stdout.write(f"{ERROR}[error]: an unexpected error occurred: {e}{RESET}\n")

def main():
    print(f"{INFO}Music Player is loading...{RESET}")
    sleep(2.0)

    url_file = resolve_path("urls.txt")
    config_file = resolve_path("config.txt")

    urls = read_urls(url_file)

    if not urls:
        sys.stdout.write(f"{HEADER}~ no tracks found ~{RESET}\n")
        
    reprint_entries(url_file)

    try:
        while True:
            volume = read_file(config_file)
            urls = read_urls(url_file)
            choice = input(f"\n{PROMPT}~ volume: {volume}% ~\n~ ready to play? type -help for commands ~\n> {RESET}")

            if choice == "-help":
                sys.stdout.write(f"\n{HEADER}[commands]{RESET}\n")
                sys.stdout.write(f"{INFO}-help                      : see this menu{RESET}\n")
                sys.stdout.write(f"{INFO}-play [number]             : play a track{RESET}\n")
                sys.stdout.write(f"{INFO}-play [number.number]      : play a track from a playlist{RESET}\n")
                sys.stdout.write(f"{INFO}CTRL + C                   : play a track{RESET}\n")
                sys.stdout.write(f"{INFO}-add [url]                 : add a track{RESET}\n")
                sys.stdout.write(f"{INFO}-remove [number,number(?)] : delete a track by its number{RESET}\n")
                sys.stdout.write(f"{INFO}-ls                        : show all tracks{RESET}\n")
                sys.stdout.write(f"{INFO}-ls [number]               : show all tracks in a playlist{RESET}\n")
                sys.stdout.write(f"{INFO}-volume [number]           : set audio volume (0 to 200){RESET}\n")
                sys.stdout.write(f"{INFO}-download [url,url(?)]     : download tracks as mp3{RESET}\n")
                sys.stdout.write(f"{INFO}-exit                      : close the program{RESET}\n")

            elif choice.startswith("-play"):
                try:
                    _, entry_number = choice.split()
                    if "." in entry_number:
                        playlist_number, track_number = entry_number.split(".")
                        playlist_number = int(playlist_number)
                        track_number = int(track_number)
                        if 1 <= playlist_number <= len(urls):
                            selected_url = get_track_url(urls[playlist_number - 1][0], track_number)
                            sys.stdout.write(f"{SUCCESS}[selecting]: playing track {playlist_number}.{track_number}{RESET}\n")
                            play_youtube_audio(selected_url, volume)
                        else:
                            sys.stdout.write(f"{ERROR}[error]: invalid track number{RESET}\n")
                    else:
                        entry_number = int(entry_number)
                        if 1 <= entry_number <= len(urls):
                            selected_url = urls[entry_number - 1][0]
                            sys.stdout.write(f"{SUCCESS}[selecting]: playing track {entry_number}{RESET}\n")
                            play_youtube_audio(selected_url, volume)
                        else:
                            sys.stdout.write(f"{ERROR}[error]: invalid track number{RESET}\n")
                except ValueError:
                    sys.stdout.write(f"{ERROR}[error]: use a valid number after -play{RESET}\n")

            elif choice.startswith("-add"):
                try:
                    _, new_urls = choice.split(maxsplit=1)
                    add_url(url_file, new_urls.split(","))
                except ValueError:
                    print(ValueError)
                    sys.stdout.write(f"{ERROR}[error]: provide a URL after -add{RESET}\n")

            elif choice.startswith("-remove"):
                try:
                    _, entry_numbers = choice.split()
                    remove_url(url_file, entry_numbers.split(","))
                except ValueError:
                    sys.stdout.write(f"{ERROR}[error]: provide a valid number after -remove{RESET}\n")

            elif choice.startswith("-ls"):
                if choice == "-ls":
                    reprint_entries(url_file)
                else:
                    try:
                        _, entry_number = choice.split() 
                        entry_number = int(entry_number)
                        if 1 <= entry_number <= len(urls):
                            selected_title = urls[entry_number - 1][1]
                            selected_url = urls[entry_number - 1][0]
                            if selected_title.startswith("[playlist]"):
                                list_video_titles(selected_url, selected_title)
                            else:
                                sys.stdout.write(f"{ERROR}[error]: provide a number of a playlist{RESET}\n")
                        else:
                            sys.stdout.write(f"{ERROR}[error]: invalid track number{RESET}\n")
                    except ValueError:
                        sys.stdout.write(f"{ERROR}[error]: provide a valid number after -ls{RESET}\n")

            elif choice.startswith("-volume"):
                try:
                    _, new_volume = choice.split()
                    if 0 <= int(new_volume) <= 200:
                        write_file(config_file, new_volume)
                        sys.stdout.write(f"{SUCCESS}[updated]: volume is now {new_volume}%{RESET}\n")
                    else:
                        sys.stdout.write(f"{ERROR}[error]: volume must be between 0 and 200{RESET}\n")
                except ValueError:
                    sys.stdout.write(f"{ERROR}[error]: enter a valid number{RESET}\n")

            elif choice == "-exit":
                sys.stdout.write(f"{SUCCESS}[exit]: shutting down{RESET}\n")
                break

            elif choice.startswith("-download"):
                _, video_urls = choice.split()
                for video_url in video_urls.split(","):
                    download_url(video_url)

            else:
                sys.stdout.write(f"{ERROR}[error]: unrecognized command{RESET}\n")
    
    except KeyboardInterrupt:
        sys.stdout.write(f"\n{ERROR}[exit]: shutting down{RESET}\n")

if __name__ == "__main__":
    main()
