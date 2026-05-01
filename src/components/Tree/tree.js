// JS module
const SVG_WIDTH = window.innerWidth;
const SVG_HEIGHT = window.innerHeight;

let svg, gContainer, treeLayout, rootNode;

// Generator for mock tree data
function generateData(nodeCount) {
  let count = 1;
  const root = { id: "root", name: "Root Idea", children: [] };
  const allNodes = [root];

  while (count < nodeCount) {
    const parentNode = allNodes[Math.floor(Math.random() * allNodes.length)];
    if (!parentNode.children) parentNode.children = [];
    
    // Add child (some are AI candidates)
    const child = { 
      id: `node-${count}`, 
      name: `Idea ${count}`,
      isAI: Math.random() > 0.8,
      children: []
    };
    parentNode.children.push(child);
    allNodes.push(child);
    count++;
  }
  return root;
}

// Draw the tree and return time taken
export function renderTree(nodeCount) {
  const startTime = performance.now();
  const data = generateData(nodeCount);

  // Clean up existing SVG
  d3.select("#tree-container").selectAll("svg").remove();

  svg = d3.select("#tree-container")
    .append("svg")
    .attr("width", SVG_WIDTH)
    .attr("height", SVG_HEIGHT)
    .call(d3.zoom().on("zoom", (event) => {
      gContainer.attr("transform", event.transform);
    }))
    .append("g")
    .attr("transform", `translate(${SVG_WIDTH/2}, 100)`);
    
  gContainer = svg; // Using gContainer for zoom/pan

  // Define layout
  const tree = d3.tree().size([SVG_WIDTH - 200, SVG_HEIGHT - 200]);
  
  // Transform to hierarchy
  const root = d3.hierarchy(data);
  treeLayout = tree(root);

  // Nodes and links
  const nodes = root.descendants();
  const links = root.links();

  // Links (Branches)
  // Use custom path for organic curve
  const linkGenerator = d3.linkVertical()
    .x(d => d.x - SVG_WIDTH/2 + 100)
    .y(d => d.y);

  gContainer.selectAll(".link")
    .data(links)
    .join("path")
    .attr("class", "link")
    .attr("d", linkGenerator)
    .attr("stroke-width", d => Math.max(1, 8 - d.source.depth)) // Variable thickness
    .attr("opacity", 0) // for initial GSAP reveal

  // Nodes (Leaves)
  const nodeGroups = gContainer.selectAll(".node")
    .data(nodes)
    .join("g")
    .attr("class", d => `node ${d.data.isAI ? 'node-ai' : ''}`)
    .attr("transform", d => `translate(${d.x - SVG_WIDTH/2 + 100},${d.y})`);

  // Simple SVG Leaf Path
  const leafPath = "M 0 0 C -15 -10 -20 -25 0 -40 C 20 -25 15 -10 0 0 Z";

  nodeGroups.append("path")
    .attr("class", "leaf-path")
    .attr("d", leafPath)
    .attr("transform", "scale(0)") // start small for growth anim

  nodeGroups.append("text")
    .attr("class", "node-text")
    .attr("dy", 15)
    .attr("text-anchor", "middle")
    .text(d => d.data.name)
    .attr("opacity", 0);

  const renderTime = performance.now() - startTime;
  document.getElementById("perf-metrics").innerText = `Render Time: ${renderTime.toFixed(2)} ms`;

  // Start Animations (GSAP)
  animateGrowth(links, nodes);
  startWindAnimation(nodeGroups);
}

function animateGrowth(links, nodes) {
  // Reveal branches
  gsap.to(".link", {
    duration: 1.5,
    opacity: 1,
    stagger: 0.05,
    ease: "power2.out"
  });

  // Grow leaves
  gsap.to(".leaf-path", {
    duration: 1,
    scale: d => 1 + Math.random() * 0.5, // Variable leaf size
    transformOrigin: "bottom center",
    stagger: 0.05,
    ease: "elastic.out(1, 0.5)",
    delay: 0.5 // after branch starts
  });

  // Reveal text
  gsap.to(".node-text", {
    duration: 1,
    opacity: 1,
    stagger: 0.05,
    delay: 1
  });
}

function startWindAnimation(nodeGroups) {
  // Gentle sway using GSAP timeline
  nodeGroups.each(function(d) {
    const el = this;
    const swayAmount = 3 + Math.random() * 4;
    const duration = 3 + Math.random() * 2;
    
    gsap.to(el, {
      rotation: swayAmount,
      transformOrigin: "bottom center",
      duration: duration,
      yoyo: true,
      repeat: -1,
      ease: "sine.inOut",
      delay: Math.random() * 2
    });
  });
}

// Setup Event Listeners
document.getElementById("btn-10").addEventListener("click", () => renderTree(10));
document.getElementById("btn-50").addEventListener("click", () => renderTree(50));
document.getElementById("btn-100").addEventListener("click", () => renderTree(100));
document.getElementById("btn-200").addEventListener("click", () => renderTree(200));
document.getElementById("btn-add").addEventListener("click", () => {
   // Simulated "Add Leaf" logic - could re-render with N+1
   // For now just re-renders 50 as an example or random
   renderTree(Math.floor(Math.random() * 50) + 10);
});

// Initial Render
renderTree(10);
