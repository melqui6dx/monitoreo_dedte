import time
import requests
import socket
import speedtest
import csv
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import platform
import asyncio

# Configuración
SITES = [
    "https://www.google.com",
    "https://www.office.com",  
    "https://chat.google.com",
    "https://www.canva.com/es_es/",
    "https://us04web.zoom.us/s",
    "https://presencial.uagrm.edu.bo/",
    "https://virtual.uagrm.edu.bo/",
    "https://meet.google.com"
    # SITIOS REQUERIDOS PARA EL SONDEO
]
DNS_SERVERS = ["172.21.1.7", "8.8.8.8"]  # Servidores DNS a probar
PORTS = [80, 443, 3389]  # Puertos a verificar (HTTP, HTTPS, RDP, por ejemplo)
INTERVAL = 180  # Intervalo de monitoreo en segundos (2 minutos)
OUTPUT_CSV = "network_monitoring_report.csv"
DURATION = 1800  # Duración total del monitoreo en segundos (1/2 hora)

# Almacenar resultados
results = {
    "timestamp": [],
    "site_latencies": {site: [] for site in SITES},
    "dns_times": {dns: [] for dns in DNS_SERVERS},
    "port_status": {port: [] for port in PORTS},
    "download_speed": [],
    "upload_speed": []
}

def check_site(site):
    """Verifica la latencia y accesibilidad de un sitio web."""
    try:
        start_time = time.time()
        response = requests.get(site, timeout=5)
        latency = (time.time() - start_time) * 1000  # Convertir a ms
        return latency if response.status_code == 200 else None
    except requests.RequestException:
        return None

def check_dns(dns_server):
    """Mide el tiempo de resolución DNS."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        start_time = time.time()
        socket.gethostbyaddr(dns_server)
        return (time.time() - start_time) * 1000  # Convertir a ms
    except socket.error:
        return None

def check_port(host, port):
    """Verifica si un puerto está abierto."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0  # True si el puerto está abierto
    except socket.error:
        return False

def measure_speed():
    """Mide la velocidad de descarga y subida."""
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        download = st.download() / 1_000_000  # Convertir a Mbps
        upload = st.upload() / 1_000_000      # Convertir a Mbps
        return download, upload
    except speedtest.SpeedtestException:
        return None, None

def save_to_csv():
    """Guarda los resultados en un archivo CSV."""
    with open(OUTPUT_CSV, mode='w', newline='') as file:
        writer = csv.writer(file)
        headers = ["Timestamp"] + [f"Latency_{site}" for site in SITES] + \
                  [f"DNS_{dns}" for dns in DNS_SERVERS] + \
                  [f"Port_{port}" for port in PORTS] + ["Download_Speed", "Upload_Speed"]
        writer.writerow(headers)
        
        for i in range(len(results["timestamp"])):
            row = [results["timestamp"][i]]
            for site in SITES:
                row.append(results["site_latencies"][site][i] or "N/A")
            for dns in DNS_SERVERS:
                row.append(results["dns_times"][dns][i] or "N/A")
            for port in PORTS:
                row.append(results["port_status"][port][i])
            row.append(results["download_speed"][i] or "N/A")
            row.append(results["upload_speed"][i] or "N/A")
            writer.writerow(row)

def plot_results():
    """Genera gráficos de latencia, DNS, y velocidad."""
    plt.figure(figsize=(12, 8))

    # Gráfico de latencia de sitios
    plt.subplot(3, 1, 1)
    for site in SITES:
        latencies = [l if l is not None else np.nan for l in results["site_latencies"][site]]
        plt.plot(results["timestamp"], latencies, label=site, marker='o')
    plt.title("Latencia de Sitios Web (ms)")
    plt.xlabel("Tiempo")
    plt.ylabel("Latencia (ms)")
    plt.legend()
    plt.grid(True)

    # Gráfico de tiempos DNS
    plt.subplot(3, 1, 2)
    for dns in DNS_SERVERS:
        times = [t if t is not None else np.nan for t in results["dns_times"][dns]]
        plt.plot(results["timestamp"], times, label=f"DNS {dns}", marker='o')
    plt.title("Tiempo de Resolución DNS (ms)")
    plt.xlabel("Tiempo")
    plt.ylabel("Tiempo (ms)")
    plt.legend()
    plt.grid(True)

    # Gráfico de velocidad
    plt.subplot(3, 1, 3)
    download_speeds = [d if d is not None else np.nan for d in results["download_speed"]]
    upload_speeds = [u if u is not None else np.nan for u in results["upload_speed"]]
    plt.plot(results["timestamp"], download_speeds, label="Descarga (Mbps)", marker='o')
    plt.plot(results["timestamp"], upload_speeds, label="Subida (Mbps)", marker='o')
    plt.title("Velocidad de Red")
    plt.xlabel("Tiempo")
    plt.ylabel("Velocidad (Mbps)")
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig("network_monitoring_plot.png")

async def main():
    """Función principal para el monitoreo."""
    start_time = time.time()
    while time.time() - start_time < DURATION:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        results["timestamp"].append(current_time)

        # Monitorear sitios web
        for site in SITES:
            latency = check_site(site)
            results["site_latencies"][site].append(latency)

        # Monitorear DNS
        for dns in DNS_SERVERS:
            dns_time = check_dns(dns)
            results["dns_times"][dns].append(dns_time)

        # Monitorear puertos
        for port in PORTS:
            status = check_port("example.com", port)  # Reemplaza con el host adecuado
            results["port_status"][port].append(status)

        # Medir velocidad (cada 15 minutos para no saturar)
        if len(results["timestamp"]) % 3 == 0:
            download, upload = measure_speed()
        else:
            download, upload = None, None
        results["download_speed"].append(download)
        results["upload_speed"].append(upload)

        # Guardar resultados
        save_to_csv()
        plot_results()

        await asyncio.sleep(INTERVAL)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())