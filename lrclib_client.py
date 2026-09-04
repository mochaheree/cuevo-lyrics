"""
Klien sederhana untuk LRCLIB API (https://lrclib.net).
Tidak butuh API key. Endpoint publik yang dipakai di sini:

  - GET /api/search  -> cari banyak kandidat lagu (bisa by query bebas,
                         atau by track_name/artist_name/album_name)
  - GET /api/get/{id} -> ambil satu entri lirik lengkap berdasarkan ID

Field penting per item hasil API: id, trackName, artistName, albumName,
duration (detik, float), instrumental (bool), plainLyrics, syncedLyrics
(string format LRC, atau null kalau tidak ada).
"""
import requests

BASE_URL = "https://lrclib.net/api"
USER_AGENT = "CuevoLyrics/1.0 (personal project)"


class LrcLibError(Exception):
    pass


def _headers():
    # LRCLIB menganjurkan (bukan wajib) mengirim User-Agent yang jelas
    return {"User-Agent": USER_AGENT}


def search(query="", track_name="", artist_name="", album_name="", timeout=10):
    """
    Cari lagu di LRCLIB. Mengembalikan list of dict mentah dari API
    (bisa kosong kalau tidak ada hasil).
    """
    params = {}
    if query:
        params["q"] = query
    if track_name:
        params["track_name"] = track_name
    if artist_name:
        params["artist_name"] = artist_name
    if album_name:
        params["album_name"] = album_name

    if not params:
        raise ValueError("Need at least 'query' or 'track_name' to search.")

    resp = requests.get(f"{BASE_URL}/search", params=params, headers=_headers(), timeout=timeout)
    if resp.status_code != 200:
        raise LrcLibError(f"Search failed (HTTP {resp.status_code}): {resp.text[:200]}")
    return resp.json()


def get_by_id(lrclib_id, timeout=10):
    """Ambil satu entri lirik lengkap berdasarkan ID hasil search()."""
    resp = requests.get(f"{BASE_URL}/get/{lrclib_id}", headers=_headers(), timeout=timeout)
    if resp.status_code == 404:
        raise LrcLibError("No lyrics found for that ID.")
    if resp.status_code != 200:
        raise LrcLibError(f"Could not fetch lyrics (HTTP {resp.status_code}): {resp.text[:200]}")
    return resp.json()


def get_exact(track_name, artist_name, album_name="", duration=None, timeout=10):
    """
    Ambil lirik dengan exact match (endpoint /api/get). LRCLIB memakai
    kombinasi track_name + artist_name + duration untuk memastikan file
    LRC-nya benar-benar cocok versi rekaman tertentu. `duration` dalam detik.
    Berguna kalau kamu sudah tahu persis metadata lagunya (mis. dari file
    musik lokal) dan mau skip langkah pencarian manual.
    """
    params = {"track_name": track_name, "artist_name": artist_name}
    if album_name:
        params["album_name"] = album_name
    if duration is not None:
        params["duration"] = int(round(duration))

    resp = requests.get(f"{BASE_URL}/get", params=params, headers=_headers(), timeout=timeout)
    if resp.status_code == 404:
        raise LrcLibError("No exact-match lyrics for these parameters.")
    if resp.status_code != 200:
        raise LrcLibError(f"Could not fetch lyrics (HTTP {resp.status_code}): {resp.text[:200]}")
    return resp.json()
