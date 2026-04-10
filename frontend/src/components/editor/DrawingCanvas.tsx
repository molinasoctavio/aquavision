"use client";
import { useState, useRef } from "react";
import { Stage, Layer, Arrow, Line, Circle, Rect, Text } from "react-konva";
import { ArrowRight, Minus, Circle as CircleIcon, Square, Pencil, Type, Trash2, Check } from "lucide-react";

type Tool = "arrow" | "line" | "circle" | "rect" | "freehand" | "text";

interface Props {
  width: number;
  height: number;
  onSave: (data: any) => void;
}

export default function DrawingCanvas({ width, height, onSave }: Props) {
  const [tool, setTool] = useState<Tool>("arrow");
  const [color, setColor] = useState("#FF0000");
  const [shapes, setShapes] = useState<any[]>([]);
  const [drawing, setDrawing] = useState(false);
  const [currentShape, setCurrentShape] = useState<any>(null);
  const stageRef = useRef<any>(null);

  const colors = ["#FF0000", "#FF9800", "#FFEB3B", "#4CAF50", "#2196F3", "#9C27B0", "#FFFFFF"];

  const handleMouseDown = (e: any) => {
    const pos = e.target.getStage().getPointerPosition();
    setDrawing(true);
    const base = { id: Date.now(), color, tool };

    if (tool === "arrow" || tool === "line") {
      setCurrentShape({ ...base, points: [pos.x, pos.y, pos.x, pos.y] });
    } else if (tool === "circle") {
      setCurrentShape({ ...base, x: pos.x, y: pos.y, radius: 0 });
    } else if (tool === "rect") {
      setCurrentShape({ ...base, x: pos.x, y: pos.y, width: 0, height: 0 });
    } else if (tool === "freehand") {
      setCurrentShape({ ...base, points: [pos.x, pos.y] });
    }
  };

  const handleMouseMove = (e: any) => {
    if (!drawing || !currentShape) return;
    const pos = e.target.getStage().getPointerPosition();

    if (tool === "arrow" || tool === "line") {
      setCurrentShape((s: any) => ({ ...s, points: [s.points[0], s.points[1], pos.x, pos.y] }));
    } else if (tool === "circle") {
      const dx = pos.x - currentShape.x;
      const dy = pos.y - currentShape.y;
      setCurrentShape((s: any) => ({ ...s, radius: Math.sqrt(dx*dx + dy*dy) }));
    } else if (tool === "rect") {
      setCurrentShape((s: any) => ({
        ...s,
        width: pos.x - s.x,
        height: pos.y - s.y,
      }));
    } else if (tool === "freehand") {
      setCurrentShape((s: any) => ({ ...s, points: [...s.points, pos.x, pos.y] }));
    }
  };

  const handleMouseUp = () => {
    if (currentShape) setShapes(prev => [...prev, currentShape]);
    setDrawing(false);
    setCurrentShape(null);
  };

  const renderShape = (s: any) => {
    if (s.tool === "arrow") return (
      <Arrow key={s.id} points={s.points} stroke={s.color} strokeWidth={3} fill={s.color} pointerLength={10} pointerWidth={8} />
    );
    if (s.tool === "line") return (
      <Line key={s.id} points={s.points} stroke={s.color} strokeWidth={3} />
    );
    if (s.tool === "circle") return (
      <Circle key={s.id} x={s.x} y={s.y} radius={s.radius} stroke={s.color} strokeWidth={3} />
    );
    if (s.tool === "rect") return (
      <Rect key={s.id} x={s.x} y={s.y} width={s.width} height={s.height} stroke={s.color} strokeWidth={3} />
    );
    if (s.tool === "freehand") return (
      <Line key={s.id} points={s.points} stroke={s.color} strokeWidth={3} tension={0.5} lineCap="round" />
    );
    return null;
  };

  return (
    <div className="absolute inset-0 z-30">
      {/* Toolbar */}
      <div className="absolute top-3 left-1/2 -translate-x-1/2 z-40 flex items-center gap-2 bg-gray-900/95 backdrop-blur border border-gray-700 rounded-xl px-3 py-2 shadow-xl">
        {([
          { id: "arrow",   icon: ArrowRight },
          { id: "line",    icon: Minus      },
          { id: "circle",  icon: CircleIcon },
          { id: "rect",    icon: Square     },
          { id: "freehand",icon: Pencil     },
        ] as const).map(({ id, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setTool(id)}
            className={`p-1.5 rounded-lg transition ${tool === id ? "bg-pool-600 text-white" : "text-gray-400 hover:text-white hover:bg-gray-700"}`}
          >
            <Icon className="w-4 h-4" />
          </button>
        ))}

        <div className="w-px h-5 bg-gray-700 mx-1" />

        {colors.map(c => (
          <button
            key={c}
            onClick={() => setColor(c)}
            className={`w-5 h-5 rounded-full border-2 transition ${color === c ? "border-white scale-110" : "border-transparent"}`}
            style={{ background: c }}
          />
        ))}

        <div className="w-px h-5 bg-gray-700 mx-1" />

        <button onClick={() => setShapes([])} className="p-1.5 text-gray-400 hover:text-red-400 rounded-lg hover:bg-gray-700 transition">
          <Trash2 className="w-4 h-4" />
        </button>
        <button
          onClick={() => onSave({ shapes, tool, color })}
          className="p-1.5 text-green-400 hover:bg-green-950 rounded-lg transition"
        >
          <Check className="w-4 h-4" />
        </button>
      </div>

      <Stage
        width={width}
        height={height}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        ref={stageRef}
        className="cursor-crosshair"
      >
        <Layer>
          {shapes.map(renderShape)}
          {currentShape && renderShape(currentShape)}
        </Layer>
      </Stage>
    </div>
  );
}
