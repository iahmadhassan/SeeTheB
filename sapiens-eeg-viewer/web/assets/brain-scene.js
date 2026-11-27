import * as THREE from "three";
import { OrbitControls } from "./three/OrbitControls.js";
import { OBJLoader } from "./three/OBJLoader.js";
import * as BufferGeometryUtils from "./three/BufferGeometryUtils.js";

const canvas = document.getElementById("brain-scene");
const status = document.getElementById("scene-status");
const panel = document.querySelector(".viewer-panel");
const scene = new THREE.Scene();
scene.background = new THREE.Color("#101721");

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;

const camera = new THREE.PerspectiveCamera(36, 1, 1, 1000);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.075;
controls.minDistance = 105;
controls.maxDistance = 480;

scene.add(new THREE.HemisphereLight(0xe4efff, 0x263344, 2.0));
const keyLight = new THREE.DirectionalLight(0xffffff, 2.5);
keyLight.position.set(-80, 120, -100);
scene.add(keyLight);
const fillLight = new THREE.DirectionalLight(0x9ab8e0, 1.1);
fillLight.position.set(100, 30, 80);
scene.add(fillLight);

const brainGroup = new THREE.Group();
scene.add(brainGroup);
const electrodeGroup = new THREE.Group();
scene.add(electrodeGroup);
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
const markers = [];
const state = { ready: false, time: 0, selected: "Fp1", values: {}, camera: "front" };
let center = new THREE.Vector3();

function resize() {
  const { width, height } = canvas.getBoundingClientRect();
  if (!width || !height) return;
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

function scenePoint(row) {
  return new THREE.Vector3(Number(row.Coord_x), Number(row.Coord_z), -Number(row.Coord_y));
}

function colorFor(value) {
  const amount = Math.min(1, Math.abs(value) / 100);
  const blue = new THREE.Color("#1766bb");
  const white = new THREE.Color("#f3f5fa");
  const red = new THREE.Color("#d51e38");
  return value < 0 ? blue.lerp(white, 1 - amount) : white.lerp(red, amount);
}

function makeLabel(label) {
  const textCanvas = document.createElement("canvas");
  textCanvas.width = 256;
  textCanvas.height = 96;
  const context = textCanvas.getContext("2d");
  context.fillStyle = "rgba(8, 13, 20, .84)";
  context.strokeStyle = "rgba(183, 199, 220, .88)";
  context.lineWidth = 5;
  context.beginPath();
  context.roundRect(4, 4, 248, 88, 18);
  context.fill();
  context.stroke();
  context.fillStyle = "#f4f7fb";
  context.font = "700 48px system-ui, sans-serif";
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.fillText(label, 128, 48);
  const texture = new THREE.CanvasTexture(textCanvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({
    map: texture,
    transparent: true,
    depthTest: false,
    depthWrite: false,
  }));
  sprite.scale.set(11, 4.2, 1);
  return sprite;
}

function parseCsv(text) {
  const [headerLine, ...lines] = text.trim().split(/\r?\n/);
  const clean = line => line.replaceAll('"', "").split(",");
  const headers = clean(headerLine);
  return lines.map(line => {
    const values = clean(line);
    return Object.fromEntries(headers.map((header, index) => [header, values[index]]));
  });
}

function setMarkerValue(marker, value) {
  marker.value = value;
  const color = colorFor(value);
  marker.mesh.material.color.copy(color);
  marker.mesh.material.emissive.copy(color);
  marker.mesh.material.emissiveIntensity = 0.48 + Math.min(1, Math.abs(value) / 100) * 0.5;
  marker.glow.material.color.copy(color);
  marker.glow.material.opacity = Math.min(0.52, Math.abs(value) / 100 * 0.52);
  marker.label.material.color.set(value < 0 ? "#acd2ff" : "#ffd0d5");
  state.values[marker.labelText] = { erd: value, color: `#${color.getHexString()}` };
}

function setTime(time) {
  if (!state.ready) return;
  const roundedTime = ((Math.round(time * 10) % 200) + 200) % 200;
  state.time = roundedTime / 10;
  for (const marker of markers) {
    setMarkerValue(marker, marker.values[roundedTime]);
  }
}

function setView(view) {
  const radius = view === "top" ? 320 : 285;
  const locations = {
    front: [0, 15, -radius],
    top: [0, radius, 0],
    left: [-radius, 12, 0],
    right: [radius, 12, 0],
  };
  const position = locations[view];
  if (!position) return;
  camera.up.set(0, 1, 0);
  if (view === "top") camera.up.set(0, 0, -1);
  camera.position.set(center.x + position[0], center.y + position[1], center.z + position[2]);
  controls.target.copy(center);
  controls.update();
  state.camera = view;
}

function selectElectrode(label) {
  state.selected = label;
  for (const marker of markers) {
    marker.mesh.scale.setScalar(marker.labelText === label ? 1.25 : 1);
  }
  window.dispatchEvent(new CustomEvent("demo-select-channel", { detail: { channel: label } }));
}

async function loadMeshes() {
  const loader = new OBJLoader();
  for (const hemisphere of ["lh", "rh"]) {
    const response = await fetch(`./assets/brains/${hemisphere}-pial.obj`);
    if (!response.ok) throw new Error(`${hemisphere} pial mesh: HTTP ${response.status}`);
    const object = loader.parse(await response.text());
    object.traverse(child => {
      if (!child.isMesh) return;
      const smoothGeometry = BufferGeometryUtils.mergeVertices(child.geometry, 1e-4);
      child.geometry.dispose();
      child.geometry = smoothGeometry;
      child.geometry.computeVertexNormals();
      child.material = new THREE.MeshStandardMaterial({
        color: 0x9aa6b5,
        roughness: 0.78,
        metalness: 0,
        transparent: true,
        opacity: 0.38,
        depthWrite: false,
        side: THREE.DoubleSide,
      });
      child.renderOrder = 1;
    });
    brainGroup.add(object);
  }
  const bounds = new THREE.Box3().setFromObject(brainGroup);
  center = bounds.getCenter(new THREE.Vector3());
  controls.target.copy(center);
  setView("front");
}

async function loadElectrodesAndValues() {
  const [electrodeResponse, valuesResponse] = await Promise.all([
    fetch("../data/electrodes.csv"),
    fetch("../data/values.csv"),
  ]);
  if (!electrodeResponse.ok) throw new Error(`electrodes.csv: HTTP ${electrodeResponse.status}`);
  if (!valuesResponse.ok) throw new Error(`values.csv: HTTP ${valuesResponse.status}`);
  const electrodes = parseCsv(await electrodeResponse.text());
  const values = parseCsv(await valuesResponse.text());
  const byElectrode = new Map();
  for (const row of values) {
    if (row.Subject !== "N27" || row.Project !== "Illustrative") continue;
    const id = Number(row.Electrode);
    if (!byElectrode.has(id)) byElectrode.set(id, Array(200).fill(0));
    const timeIndex = Math.round(Number(row.Time) * 10) % 200;
    byElectrode.get(id)[timeIndex] = Number(row.ERD_percent);
  }

  const sphereGeometry = new THREE.SphereGeometry(3, 24, 16);
  const glowGeometry = new THREE.SphereGeometry(4.5, 20, 12);
  for (const row of electrodes) {
    const label = row.Label;
    const valuesForElectrode = byElectrode.get(Number(row.Electrode));
    if (!valuesForElectrode) throw new Error(`No N27 values for electrode ${row.Electrode} (${label})`);
    const position = scenePoint(row);
    const material = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      emissive: 0xffffff,
      emissiveIntensity: 0.7,
      roughness: 0.28,
      metalness: 0,
    });
    const mesh = new THREE.Mesh(sphereGeometry, material);
    mesh.position.copy(position);
    mesh.userData.label = label;
    mesh.renderOrder = 2;
    electrodeGroup.add(mesh);

    const glow = new THREE.Mesh(glowGeometry, new THREE.MeshBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    }));
    glow.position.copy(position);
    glow.renderOrder = 2;
    electrodeGroup.add(glow);

    const labelSprite = makeLabel(label);
    labelSprite.position.copy(position).add(new THREE.Vector3(0, 6, 0));
    labelSprite.renderOrder = 3;
    electrodeGroup.add(labelSprite);

    markers.push({
      labelText: label,
      mesh,
      glow,
      label: labelSprite,
      values: valuesForElectrode,
      value: 0,
    });
  }
}

canvas.addEventListener("pointerdown", event => {
  const rect = canvas.getBoundingClientRect();
  pointer.set(
    ((event.clientX - rect.left) / rect.width) * 2 - 1,
    -((event.clientY - rect.top) / rect.height) * 2 + 1,
  );
  raycaster.setFromCamera(pointer, camera);
  const hit = raycaster.intersectObjects(markers.map(marker => marker.mesh), false)[0];
  if (hit) selectElectrode(hit.object.userData.label);
});

for (const button of document.querySelectorAll(".view-button")) {
  button.addEventListener("click", () => setView(button.dataset.view));
}

for (const [tabId, mode] of [["scene-tab", "scene"], ["threebrain-tab", "threebrain"]]) {
  document.getElementById(tabId).addEventListener("click", () => {
    panel.dataset.mode = mode;
    document.getElementById("scene-tab").setAttribute("aria-selected", String(mode === "scene"));
    document.getElementById("threebrain-tab").setAttribute("aria-selected", String(mode === "threebrain"));
    document.querySelector(".about").open = false;
    window.dispatchEvent(new CustomEvent("demo-viewer-tab", { detail: { active: mode === "threebrain" } }));
    resize();
  });
}

window.addEventListener("demo-time", event => setTime(event.detail.time));
window.addEventListener("demo-select-channel", event => {
  state.selected = event.detail.channel;
  for (const marker of markers) {
    marker.mesh.scale.setScalar(marker.labelText === state.selected ? 1.25 : 1);
  }
});
window.eegScene = {
  getState: () => ({
    ready: state.ready,
    time: state.time,
    selected: state.selected,
    values: { ...state.values },
    camera: state.camera,
    electrodeCount: markers.length,
  }),
  setView,
};

new ResizeObserver(resize).observe(canvas);
window.addEventListener("resize", resize);

Promise.all([loadMeshes(), loadElectrodesAndValues()])
  .then(() => {
    state.ready = true;
    setTime(window.demoCurrentTime || 0);
    selectElectrode(state.selected);
    status.textContent = "N27 pial · 15 contacts · drag to orbit";
    resize();
  })
  .catch(error => {
    status.textContent = `3D scene failed: ${error.message}`;
    console.error(error);
  });

function render() {
  controls.update();
  renderer.render(scene, camera);
  requestAnimationFrame(render);
}

render();
