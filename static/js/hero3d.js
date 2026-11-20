// The 3D cash flow scene at the top of the dashboard.
// Bars are the real monthly totals, the floating card shows this month's
// collected amount, and a few coins orbit around it. It's decoration, so it stays light:
// it pauses when the tab is hidden and stays still for people who've
// asked their system to reduce motion.

import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js";

const canvas = document.getElementById("hero-canvas");
const months = JSON.parse(document.getElementById("monthly-data").textContent);
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const MINT = 0x5ec2a6;
const MINT_DARK = 0x2a6b5a;
const GOLD = 0xd9b56a;

let renderer;
try {
  renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
} catch (error) {
  // No WebGL (old laptop, remote desktop...). The rest of the hero still works.
  canvas.remove();
}

if (renderer) {
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(0x000000, 0);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 100);
  camera.position.set(5.2, 3.8, 11.4);
  camera.lookAt(0.6, 1.55, 0);

  scene.add(new THREE.HemisphereLight(0xdff7ee, 0x0f131a, 1.1));
  const sun = new THREE.DirectionalLight(0xffffff, 1.4);
  sun.position.set(5, 9, 6);
  scene.add(sun);

  // Everything sits on one group so the whole scene can sway gently.
  const world = new THREE.Group();
  scene.add(world);

  const base = new THREE.Mesh(
    new THREE.BoxGeometry(6.6, 0.16, 2.2),
    new THREE.MeshStandardMaterial({ color: 0x1b222c, roughness: 0.9 })
  );
  base.position.set(-0.7, 0, 0);
  world.add(base);

  // Bars: the tallest month is 3.2 units high, the rest are scaled to it.
  let highest = 0;
  for (let i = 0; i < months.length; i++) {
    if (months[i].value > highest) {
      highest = months[i].value;
    }
  }

  const bars = [];
  for (let i = 0; i < months.length; i++) {
    const isCurrent = i === months.length - 1;
    const material = new THREE.MeshStandardMaterial({
      color: isCurrent ? MINT : MINT_DARK,
      roughness: 0.35,
      metalness: 0.1,
      emissive: isCurrent ? 0x0d3b30 : 0x000000,
    });
    const bar = new THREE.Mesh(new THREE.BoxGeometry(0.62, 1, 0.62), material);

    let height = 0.08;
    if (highest > 0) {
      height = Math.max((months[i].value / highest) * 3.2, 0.08);
    }

    bar.position.set(-3.2 + i * 1.0, 0.08, 0);
    bar.userData.height = height;
    world.add(bar);
    bars.push(bar);
  }

  // The floating invoice, drawn onto a canvas and used as a texture.
  const paper = document.createElement("canvas");
  paper.width = 256;
  paper.height = 340;
  const pen = paper.getContext("2d");
  pen.fillStyle = "#fbfaf7";
  pen.fillRect(0, 0, 256, 340);
  pen.fillStyle = "#0f8a6a";
  pen.font = "600 24px Sora, sans-serif";
  pen.fillText("Invoice", 24, 46);
  pen.fillStyle = "#e6e3dc";
  for (let i = 0; i < 5; i++) {
    pen.fillRect(24, 90 + i * 28, i % 2 === 0 ? 208 : 140, 10);
  }
  pen.fillStyle = "#1d2129";
  pen.font = "600 22px Sora, sans-serif";
  pen.fillText(canvas.dataset.total, 24, 268);
  pen.strokeStyle = "#0f8a6a";
  pen.lineWidth = 4;
  pen.save();
  pen.translate(182, 296);
  pen.rotate(-0.22);
  pen.strokeRect(-46, -19, 92, 38);
  pen.fillStyle = "#0f8a6a";
  pen.font = "700 19px Sora, sans-serif";
  pen.textAlign = "center";
  pen.fillText("PAID", 0, 7);
  pen.restore();

  const texture = new THREE.CanvasTexture(paper);
  texture.colorSpace = THREE.SRGBColorSpace;

  const edge = new THREE.MeshStandardMaterial({ color: 0xe9e6df });
  const face = new THREE.MeshStandardMaterial({ map: texture, roughness: 0.7 });
  // A box has six faces; index 4 is the one facing the camera.
  const card = new THREE.Mesh(new THREE.BoxGeometry(1.5, 2.0, 0.04), [edge, edge, edge, edge, face, edge]);
  card.position.set(3.5, 2.2, 0.4);
  world.add(card);

  const coins = [];
  const coinShape = new THREE.CylinderGeometry(0.2, 0.2, 0.06, 32);
  const coinMaterial = new THREE.MeshStandardMaterial({ color: GOLD, metalness: 0.7, roughness: 0.3 });
  for (let i = 0; i < 5; i++) {
    const coin = new THREE.Mesh(coinShape, coinMaterial);
    coin.userData.offset = (i / 5) * Math.PI * 2;
    world.add(coin);
    coins.push(coin);
  }

  function resize() {
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  }
  new ResizeObserver(resize).observe(canvas);
  resize();

  // Ease-out so the bars slow down as they reach full height.
  function easeOut(t) {
    return 1 - Math.pow(1 - t, 3);
  }

  function draw(seconds) {
    for (let i = 0; i < bars.length; i++) {
      let progress = 1;
      if (!reduceMotion) {
        progress = Math.min(Math.max((seconds - i * 0.15) / 1.1, 0), 1);
      }
      const height = bars[i].userData.height * easeOut(progress);
      bars[i].scale.y = Math.max(height, 0.001);
      bars[i].position.y = 0.08 + height / 2;
    }

    card.position.y = 2.2 + Math.sin(seconds * 1.2) * 0.12;
    card.rotation.y = -0.5 + Math.sin(seconds * 0.6) * 0.15;

    for (let i = 0; i < coins.length; i++) {
      const angle = seconds * 0.9 + coins[i].userData.offset;
      coins[i].position.set(
        3.5 + Math.cos(angle) * 1.3,
        2.2 + Math.sin(angle * 2) * 0.25,
        0.4 + Math.sin(angle) * 1.3
      );
      coins[i].rotation.set(Math.PI / 2, 0, angle * 2);
    }

    world.rotation.y = Math.sin(seconds * 0.25) * 0.12;
    renderer.render(scene, camera);
  }

  if (reduceMotion) {
    draw(2);
  } else {
    const clock = new THREE.Clock();
    renderer.setAnimationLoop(function () {
      draw(clock.getElapsedTime());
    });

    // No point drawing frames nobody can see.
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) {
        renderer.setAnimationLoop(null);
      } else {
        renderer.setAnimationLoop(function () {
          draw(clock.getElapsedTime());
        });
      }
    });
  }
}
