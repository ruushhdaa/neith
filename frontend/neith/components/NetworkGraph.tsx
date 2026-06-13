"use client";

import { useEffect, useRef } from "react";
import * as d3 from "d3";
import { NeithNode, NeithEdge } from "@/hooks/useNeith";

interface Props {
  nodes: NeithNode[];
  edges: NeithEdge[];
  fullscreen?: boolean;
}

export default function NetworkGraph({ nodes, edges, fullscreen = false }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!nodes.length || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;

    svg.selectAll("*").remove();

    const simNodes: any[] = nodes.map(n => ({ ...n }));
    const simLinks: any[] = edges.map(e => ({ ...e }));

    const simulation = d3.forceSimulation(simNodes)
      .force("link", d3.forceLink(simLinks).id((d: any) => d.id).distance(110).strength(0.08))
      .force("charge", d3.forceManyBody().strength(-280))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(35));

    // Glow filter
    const defs = svg.append("defs");
    const glowFilter = defs.append("filter").attr("id", "glow");
    glowFilter.append("feGaussianBlur").attr("stdDeviation", "4").attr("result", "coloredBlur");
    const feMerge = glowFilter.append("feMerge");
    feMerge.append("feMergeNode").attr("in", "coloredBlur");
    feMerge.append("feMergeNode").attr("in", "SourceGraphic");

    // Stronger glow for suspicious
    const strongGlow = defs.append("filter").attr("id", "strong-glow");
    strongGlow.append("feGaussianBlur").attr("stdDeviation", "8").attr("result", "coloredBlur");
    const feMerge2 = strongGlow.append("feMerge");
    feMerge2.append("feMergeNode").attr("in", "coloredBlur");
    feMerge2.append("feMergeNode").attr("in", "SourceGraphic");

    // Links — animated dashes
    const link = svg.append("g")
      .selectAll("line")
      .data(simLinks)
      .enter()
      .append("line")
      .attr("stroke", "rgba(187,104,48,0.2)")
      .attr("stroke-width", 1)
      .attr("stroke-dasharray", "4 4")
      .style("animation", "edge-flow 2s linear infinite");

    // Node groups
    const nodeG = svg.append("g")
      .selectAll("g")
      .data(simNodes)
      .enter()
      .append("g")
      .style("cursor", "pointer")
      .call(
        d3.drag<any, any>()
          .on("start", (e, d) => { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
          .on("drag",  (e, d) => { d.fx = e.x; d.fy = e.y; })
          .on("end",   (e, d) => { if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; })
      );

    // Outer pulse ring for suspicious — multiple layers
    nodeG.filter((d: any) => d.status === "suspicious")
      .append("circle")
      .attr("r", 28)
      .attr("fill", "none")
      .attr("stroke", "#BB6830")
      .attr("stroke-width", 1)
      .attr("opacity", 0.2)
      .style("animation", "node-pulse 3s ease-in-out infinite");

    nodeG.filter((d: any) => d.status === "suspicious")
      .append("circle")
      .attr("r", 22)
      .attr("fill", "none")
      .attr("stroke", "#F8E794")
      .attr("stroke-width", 0.5)
      .attr("opacity", 0.3)
      .style("animation", "node-pulse 2s ease-in-out infinite 0.5s");

    // Main node circle
    nodeG.append("circle")
      .attr("r", 14)
      .attr("fill", (d: any) => d.status === "suspicious"
        ? "rgba(133,67,30,0.9)"
        : "rgba(40,65,57,0.85)")
      .attr("stroke", (d: any) => d.status === "suspicious" ? "#BB6830" : "rgba(187,104,48,0.35)")
      .attr("stroke-width", 1.5)
      .attr("filter", (d: any) => d.status === "suspicious" ? "url(#strong-glow)" : "url(#glow)")
      .on("mouseenter", function() {
        d3.select(this).transition().duration(200).attr("r", 18);
      })
      .on("mouseleave", function() {
        d3.select(this).transition().duration(200).attr("r", 14);
      });

    // Inner dot for suspicious
    nodeG.filter((d: any) => d.status === "suspicious")
      .append("circle")
      .attr("r", 3)
      .attr("fill", "#F8E794")
      .attr("opacity", 0.8);

    // Score text inside
    nodeG.append("text")
      .text((d: any) => `${(d.score * 100).toFixed(0)}`)
      .attr("text-anchor", "middle")
      .attr("dy", 4)
      .attr("font-size", "9px")
      .attr("font-family", "Cinzel, serif")
      .attr("fill", "#F8E794")
      .attr("pointer-events", "none");

    // IP label below
    nodeG.append("text")
      .text((d: any) => d.id.split(".").slice(-2).join("."))
      .attr("text-anchor", "middle")
      .attr("dy", 30)
      .attr("font-size", "9px")
      .attr("font-family", "Cinzel, serif")
      .attr("fill", "#809070")
      .attr("pointer-events", "none");

    // Connection count label above
    nodeG.append("text")
      .text((d: any) => {
        const count = simLinks.filter(
          (l: any) => (l.source?.id || l.source) === d.id || (l.target?.id || l.target) === d.id
        ).length;
        return count > 1 ? `${count} flows` : "";
      })
      .attr("text-anchor", "middle")
      .attr("dy", -22)
      .attr("font-size", "8px")
      .attr("font-family", "Cinzel, serif")
      .attr("fill", "rgba(187,104,48,0.5)")
      .attr("pointer-events", "none");

    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      nodeG.attr("transform", (d: any) => `translate(${d.x},${d.y})`);
    });

    return () => { simulation.stop(); };
  }, [nodes, edges]);

  return (
    <svg
      ref={svgRef}
      style={{ width: "100%", height: "100%", background: "transparent" }}
    />
  );
}