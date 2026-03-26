from flask import Flask, render_template
import numpy as np
import folium
from geopy.distance import geodesic

app = Flask(__name__)

# ==============================
# 1. Locations in Alexandria
# ==============================
locations = {
    "Montaza": (31.2904, 30.0126),
    "Stanley": (31.2450, 29.9660),
    "Smouha": (31.2156, 29.9553),
    "Sporting": (31.2304, 29.9577),
    "Gleem": (31.2394, 29.9570)
}

names = list(locations.keys())
coords = list(locations.values())
N = len(coords)

# ==============================
# 2. Distance Matrix (km)
# ==============================
dist = np.zeros((N, N))
for i in range(N):
    for j in range(N):
        if i == j:
            dist[i][j] = 0
        else:
            dist[i][j] = geodesic(coords[i], coords[j]).km

# ==============================
# 3. ACO Parameters
# ==============================
alpha = 1
beta = 2
rho = 0.5
Q = 100
ants = 10
iterations = 20
pher = np.ones((N, N))

# ==============================
# 4. Helper Functions
# ==============================
def path_length(path):
    return sum(dist[path[i]][path[i+1]] for i in range(len(path)-1))

def next_city(curr, visited):
    probs = []
    for j in range(N):
        if j not in visited:
            p = (pher[curr][j]**alpha) * ((1/dist[curr][j])**beta)
            probs.append((j, p))
    total = sum(p for _, p in probs)
    r = np.random.rand()
    s = 0
    for city, p in probs:
        s += p / total
        if r <= s:
            return city

# ==============================
# 5. Run ACO
# ==============================
def run_aco():
    global pher
    best_path = None
    best_len = float('inf')

    for it in range(iterations):
        paths = []

        for _ in range(ants):
            path = [np.random.randint(N)]
            while len(path) < N:
                path.append(next_city(path[-1], path))
            path.append(path[0])
            l = path_length(path)
            paths.append((path, l))
            if l < best_len:
                best_path = path
                best_len = l

        # evaporation
        pher *= (1 - rho)

        # pheromone deposit
        for path, l in paths:
            for i in range(len(path)-1):
                a, b = path[i], path[i+1]
                pher[a][b] += Q / l

    return best_path, best_len

# ==============================
# 6. Flask Routes
# ==============================
@app.route('/')
def index():
    best_path, best_len = run_aco()

    # create Folium map
    m = folium.Map(location=coords[0], zoom_start=13)
    for name, coord in locations.items():
        folium.Marker(coord, popup=name).add_to(m)

    for i in range(len(best_path)-1):
        a = coords[best_path[i]]
        b = coords[best_path[i+1]]
        folium.PolyLine([a, b], color="blue", weight=5).add_to(m)

    # render map in HTML
    map_html = m._repr_html_()
    path_names = [names[i] for i in best_path]

    return render_template('index.html', map_html=map_html, path=path_names, distance=round(best_len,2))

# ==============================
# 7. Run App
# ==============================
if __name__ == "__main__":
    app.run(debug=True, port=5001)