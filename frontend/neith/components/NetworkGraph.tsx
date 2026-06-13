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
      .force("link", d3.forceLink(simLinks).id((d: any) => d.id).distance(100).strength(0.08))
      .force("charge", d3.forceManyBody().strength(-250))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(30));

    // Pulse keyframe via filter
    const defs = svg.append("defs");
    const filter = defs.append("filter").attr("id", "glow");
    filter.append("feGaussianBlur").attr("stdDeviation", "4").attr("result", "coloredBlur");
    const feMerge = filter.append("feMerge");
    feMerge.append("feMergeNode").attr("in", "coloredBlur");
    feMerge.append("feMergeNode").attr("in", "SourceGraphic");

    // Links
    const link = svg.append("g")
      .selectAll("line")
      .data(simLinks)
      .enter()
      .append("line")
      .attr("stroke", "rgba(187,104,48,0.15)")
      .attr("stroke-width", 1);

    // Node groups
    const nodeG = svg.append("g")
      .selectAll("g")
      .data(simNodes)
      .enter()
      .append("g")
      .call(
        d3.drag<any, any>()
          .on("start", (e, d) => { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
          .on("drag",  (e, d) => { d.fx = e.x; d.fy = e.y; })
          .on("end",   (e, d) => { if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; })
      );

    // Outer pulse ring for suspicious
    nodeG.filter((d: any) => d.status === "suspicious")
      .append("circle")
      .attr("r", 22)
      .attr("fill", "none")
      .attr("stroke", "#BB6830")
      .attr("stroke-width", 1)
      .attr("opacity", 0.4)
      .style("animation", "pulse 2s ease-in-out infinite");

    // Main node circle
    nodeG.append("circle")
      .attr("r", 14)
      .attr("fill", (d: any) => d.status === "suspicious"
        ? "rgba(133,67,30,0.9)"
        : "rgba(40,65,57,0.8)")
      .attr("stroke", (d: any) => d.status === "suspicious" ? "#BB6830" : "rgba(187,104,48,0.4)")
      .attr("stroke-width", 1.5)
      .attr("filter", (d: any) => d.status === "suspicious" ? "url(#glow)" : "none");

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
      .attr("dy", 28)
      .attr("font-size", "9px")
      .attr("font-family", "Cinzel, serif")
      .attr("fill", "#809070")
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
