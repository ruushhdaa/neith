// src/components/NetworkGraph.js
// D3 force-directed network graph

import { useEffect, useRef } from "react";
import * as d3 from "d3";

export default function NetworkGraph({ graph }) {
  const svgRef = useRef(null);

  useEffect(() => {
    if (!graph.nodes.length) return;

    const svg    = d3.select(svgRef.current);
    const width  = svgRef.current.clientWidth  || 600;
    const height = svgRef.current.clientHeight || 400;

    svg.selectAll("*").remove();

    // Defs — arrow marker
    const defs = svg.append("defs");
    defs.append("marker")
      .attr("id",           "arrow")
      .attr("viewBox",      "0 -5 10 10")
      .attr("refX",         20)
      .attr("refY",         0)
      .attr("markerWidth",  6)
      .attr("markerHeight", 6)
      .attr("orient",       "auto")
      .append("path")
        .attr("d",    "M0,-5L10,0L0,5")
        .attr("fill", "#1e3a5f");

    const nodes = graph.nodes.map(n => ({ ...n }));
    const edges = graph.edges.map(e => ({ ...e }));

    const simulation = d3.forceSimulation(nodes)
      .force("link",   d3.forceLink(edges)
                          .id(d => d.id)
                          .distance(120))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide(40));

    // Edges
    const link = svg.append("g")
      .selectAll("line")
      .data(edges)
      .enter()
      .append("line")
        .attr("stroke",       "#1e3a5f")
        .attr("stroke-width", 1.5)
        .attr("marker-end",   "url(#arrow)");

    // Node groups
    const node = svg.append("g")
      .selectAll("g")
      .data(nodes)
      .enter()
      .append("g")
        .call(d3.drag()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x; d.fy = d.y;
          })
          .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
          .on("end",  (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null; d.fy = null;
          })
        );

    // Outer glow ring for suspicious nodes
    node.filter(d => d.status === "suspicious")
      .append("circle")
        .attr("r",           22)
        .attr("fill",        "none")
        .attr("stroke",      "#ff3366")
        .attr("stroke-width", 1)
        .attr("opacity",     0.4)
        .attr("class",       "pulse");

    // Main circle
    node.append("circle")
      .attr("r",      14)
      .attr("fill",   d => d.status === "suspicious" ? "#ff3366" : "#00ff88")
      .attr("opacity", 0.9)
      .attr("stroke",      d => d.status === "suspicious" ? "#ff6688" : "#00ffaa")
      .attr("stroke-width", 1.5);

    // IP label
    node.append("text")
      .text(d => d.id.split(".").slice(-2).join("."))
      .attr("text-anchor", "middle")
      .attr("dy",          30)
      .attr("font-size",   "10px")
      .attr("font-family", "Courier New")
      .attr("fill",        "#e0e0e0");

    // Score label inside circle
    node.append("text")
      .text(d => d.score.toFixed(2))
      .attr("text-anchor", "middle")
      .attr("dy",          4)
      .attr("font-size",   "9px")
      .attr("font-family", "Courier New")
      .attr("fill",        "#0a0e1a")
      .attr("font-weight", "bold");

    // Tick
    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      node.attr("transform", d => `translate(${d.x},${d.y})`);
    });

    return () => simulation.stop();
  }, [graph]);

  return (
    <div className="card" style={{ height: "100%" }}>
      <div className="card-title">Live Network Graph</div>
      <svg
        ref={svgRef}
        style={{ width: "100%", height: "calc(100% - 30px)" }}
      />
    </div>
  );
}