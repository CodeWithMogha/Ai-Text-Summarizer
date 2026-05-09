"use client";

import { useState, useRef, DragEvent } from "react";
import {
  FileText, FileUp, Video, Link2, Upload, Sparkles, Copy, Download,
  ChevronDown, MoreHorizontal, Clock, LayoutDashboard, History, Loader2,
} from "lucide-react";
import {
  summarizeText, summarizePDF, summarizeVideoURL, summarizeVideoUpload,
} from "@/lib/api";
import { SummaryLength } from "@/lib/types";

type InputMode = "text" | "pdf" | "video";
type VideoTab = "url" | "upload";
type SummaryStyle = "paragraph" | "bullets";



export default function Home() {
  const [activeMode, setActiveMode] = useState<InputMode>("text");
  const [videoTab, setVideoTab] = useState<VideoTab>("url");
  const [urlInput, setUrlInput] = useState("");
  const [textInput, setTextInput] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [summaryLength, setSummaryLength] = useState<SummaryLength>("medium");
  const [summaryStyle, setSummaryStyle] = useState<SummaryStyle>("paragraph");
  const [isLoading, setIsLoading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [summary, setSummary] = useState("");
  const [keyPoints, setKeyPoints] = useState<string[]>([]);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleGenerate = async () => {
    setIsLoading(true);
    setError(null);
    try {
      let result: { summary: string };
      if (activeMode === "text") {
        result = await summarizeText(textInput, summaryLength, summaryStyle);
      } else if (activeMode === "pdf") {
        if (!selectedFile) throw new Error("Please select a PDF file.");
        result = await summarizePDF(selectedFile, summaryLength, summaryStyle);
      } else {
        if (videoTab === "url") {
          result = await summarizeVideoURL(urlInput, summaryLength, summaryStyle);
        } else {
          if (!selectedFile) throw new Error("Please select a video file.");
          result = await summarizeVideoUpload(selectedFile, summaryLength, summaryStyle);
        }
      }
      setSummary(result.summary);
      setKeyPoints([]); // Never artificially create bullet points
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([summary], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `summary_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const handleFileDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) setSelectedFile(f);
  };

  const sidebarItems = [
    { label: "Dashboard", icon: LayoutDashboard, active: false },
    { label: "divider", icon: null, active: false },
    { label: "SUMMARIZE", icon: null, active: false, isHeader: true },
    { label: "Text", icon: FileText, active: activeMode === "text", mode: "text" as InputMode },
    { label: "PDF", icon: FileUp, active: activeMode === "pdf", mode: "pdf" as InputMode },
    { label: "Video", icon: Video, active: activeMode === "video", mode: "video" as InputMode, badge: "New" },
  ];

  const modes = [
    { id: "text" as InputMode, icon: FileText, title: "Text", desc: "Paste or type your text", color: "text-blue-600", bg: "bg-blue-50" },
    { id: "pdf" as InputMode, icon: FileUp, title: "PDF", desc: "Upload a PDF document", color: "text-orange-600", bg: "bg-orange-50" },
    { id: "video" as InputMode, icon: Video, title: "Video", desc: "Upload or paste a video link", color: "text-violet-600", bg: "bg-violet-50" },
  ];

  const readTime = Math.max(1, Math.ceil(summary.split(" ").length / 200));

  return (
    <div className="flex h-screen overflow-hidden">
      {/* ═══ SIDEBAR ═══ */}
      <aside className="w-[240px] min-w-[240px] bg-[#0F1117] flex flex-col border-r border-white/5">
        {/* Logo */}
        <div className="px-5 py-5 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center">
            <Sparkles size={16} className="text-white" />
          </div>
          <div>
            <p className="text-white text-[15px] font-semibold leading-tight">AI Summarizer</p>
            <p className="text-[#5A5E73] text-[11px]">Summarize anything</p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-2 space-y-0.5 overflow-y-auto">
          {sidebarItems.map((item, i) => {
            if (item.label.startsWith("divider")) return <div key={i} className="my-3 border-t border-white/5" />;
            if (item.isHeader) return <p key={i} className="px-3 pt-4 pb-2 text-[10px] font-semibold text-[#4A4E63] uppercase tracking-[1.5px]">{item.label}</p>;
            const Icon = item.icon!;
            return (
              <button
                key={item.label}
                onClick={() => item.mode && setActiveMode(item.mode)}
                className={`w-full flex items-center gap-3 px-3 h-9 rounded-md text-[13px] font-medium transition-all duration-200 group
                  ${item.active
                    ? "bg-[rgba(79,70,229,0.12)] text-white border-l-2 border-[#4F46E5] -ml-px"
                    : "text-[#8B8FA3] hover:text-[#C0C3D1] hover:bg-[rgba(255,255,255,0.04)]"
                  }`}
              >
                <Icon size={16} strokeWidth={1.8} className={item.active ? "text-[#818CF8]" : "text-[#5A5E73] group-hover:text-[#8B8FA3]"} />
                {item.label}
                {item.badge && (
                  <span className="ml-auto px-1.5 py-0.5 text-[9px] font-bold uppercase rounded bg-emerald-500/15 text-emerald-400 tracking-wide">{item.badge}</span>
                )}
              </button>
            );
          })}
        </nav>

        {/* User */}
        <div className="px-4 py-4 border-t border-white/5 flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white text-xs font-bold">A</div>
          <div className="flex-1 min-w-0">
            <p className="text-[13px] text-white font-medium truncate">Amitesh Mogha</p>
            <p className="text-[11px] text-[#5A5E73] truncate">amitesh@email.com</p>
          </div>
        </div>
      </aside>

      {/* ═══ MAIN CONTENT ═══ */}
      <main className="flex-1 overflow-y-auto bg-[#F8F9FB]">
        <div className="max-w-[1200px] mx-auto px-8 py-6">
          {/* Header */}
          <div className="flex items-start justify-between mb-8">
            <div>
              <h1 className="text-[22px] font-bold text-gray-900">Hello, Amitesh 👋</h1>
              <p className="text-sm text-gray-500 mt-0.5">Get concise insights from text, documents, or videos in seconds.</p>
            </div>
          </div>

          {/* Mode Selector Cards */}
          <div className="grid grid-cols-3 gap-4 mb-8">
            {modes.map(m => (
              <button
                key={m.id}
                onClick={() => { setActiveMode(m.id); setSelectedFile(null); setError(null); }}
                className={`flex items-center gap-4 p-4 rounded-xl border transition-all duration-200 text-left
                  ${activeMode === m.id
                    ? "bg-white border-[#4F46E5]/30 shadow-sm ring-1 ring-[#4F46E5]/10"
                    : "bg-white border-gray-200 hover:border-gray-300"
                  }`}
              >
                <div className={`w-10 h-10 rounded-lg ${m.bg} ${m.color} flex items-center justify-center flex-shrink-0`}>
                  <m.icon size={18} strokeWidth={1.8} />
                </div>
                <div>
                  <p className={`text-[14px] font-semibold ${activeMode === m.id ? "text-gray-900" : "text-gray-700"}`}>{m.title}</p>
                  <p className="text-[12px] text-gray-400">{m.desc}</p>
                </div>
              </button>
            ))}
          </div>

          {/* Two-Column Workspace */}
          <div className="grid grid-cols-2 gap-6 mb-8">
            {/* ── LEFT: Input Panel ── */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              {/* TEXT MODE */}
              {activeMode === "text" && (
                <div className="animate-fade-in">
                  <textarea
                    value={textInput}
                    onChange={e => setTextInput(e.target.value)}
                    placeholder="Paste or type your text here..."
                    className="w-full h-48 p-4 rounded-lg border border-gray-200 text-[14px] text-gray-800 placeholder:text-gray-400 focus:outline-none focus:border-[#4F46E5] focus:ring-1 focus:ring-[#4F46E5]/20 resize-none leading-relaxed"
                  />
                  <p className="text-right text-[11px] text-gray-400 mt-1">{textInput.length.toLocaleString()} / 100,000</p>
                </div>
              )}

              {/* PDF MODE */}
              {activeMode === "pdf" && (
                <div className="animate-fade-in">
                  <div
                    className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${isDragging ? "border-[#4F46E5] bg-indigo-50/50" : "border-gray-200 hover:border-gray-300"}`}
                    onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
                    onDragLeave={() => setIsDragging(false)}
                    onDrop={handleFileDrop}
                    onClick={() => fileRef.current?.click()}
                  >
                    <input ref={fileRef} type="file" accept=".pdf" className="hidden" onChange={e => { if (e.target.files?.[0]) setSelectedFile(e.target.files[0]); }} />
                    {selectedFile ? (
                      <div>
                        <FileUp size={28} className="mx-auto mb-3 text-[#4F46E5]" />
                        <p className="text-[14px] font-medium text-gray-800">{selectedFile.name}</p>
                        <p className="text-[12px] text-gray-400 mt-1">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                        <button onClick={e => { e.stopPropagation(); setSelectedFile(null); }} className="text-[12px] text-red-500 mt-2 hover:underline">Remove</button>
                      </div>
                    ) : (
                      <div>
                        <Upload size={28} className="mx-auto mb-3 text-gray-300" />
                        <p className="text-[14px] font-medium text-gray-600">Drop your PDF here or click to browse</p>
                        <p className="text-[12px] text-gray-400 mt-1">PDF files up to 10MB</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* VIDEO MODE */}
              {activeMode === "video" && (
                <div className="animate-fade-in">
                  <div className="flex mb-5">
                    {(["url", "upload"] as VideoTab[]).map(tab => (
                      <button
                        key={tab}
                        onClick={() => { setVideoTab(tab); setSelectedFile(null); }}
                        className={`px-5 py-2 text-[13px] font-medium border-b-2 transition-colors ${
                          videoTab === tab
                            ? "border-[#4F46E5] text-[#4F46E5]"
                            : "border-transparent text-gray-400 hover:text-gray-600"
                        }`}
                      >
                        {tab === "url" ? "URL" : "Upload File"}
                      </button>
                    ))}
                  </div>

                  {videoTab === "url" ? (
                    <div>
                      <label className="text-[13px] font-medium text-gray-700 mb-2 block">Paste YouTube link</label>
                      <div className="flex gap-2">
                        <div className="flex-1 flex items-center gap-2 h-10 px-3 rounded-lg border border-gray-200 focus-within:border-[#4F46E5] focus-within:ring-1 focus-within:ring-[#4F46E5]/20 transition-all">
                          <Link2 size={14} className="text-gray-400 flex-shrink-0" />
                          <input
                            value={urlInput}
                            onChange={e => setUrlInput(e.target.value)}
                            placeholder="https://www.youtube.com/watch?v=..."
                            className="flex-1 h-full text-[13px] text-gray-800 placeholder:text-gray-400 outline-none bg-transparent"
                          />
                        </div>
                      </div>
                      <p className="text-center text-[12px] text-gray-400 my-4">or</p>
                      <div
                        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors ${isDragging ? "border-[#4F46E5] bg-indigo-50/50" : "border-gray-200 hover:border-gray-300"}`}
                        onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
                        onDragLeave={() => setIsDragging(false)}
                        onDrop={handleFileDrop}
                        onClick={() => fileRef.current?.click()}
                      >
                        <input ref={fileRef} type="file" accept=".mp4,.mkv,.avi,.mov,.webm,.mp3,.wav" className="hidden" onChange={e => { if (e.target.files?.[0]) setSelectedFile(e.target.files[0]); }} />
                        <Upload size={22} className="mx-auto mb-2 text-gray-300" />
                        <p className="text-[13px] text-gray-500 font-medium">Upload Video File</p>
                        <p className="text-[11px] text-gray-400 mt-1">MP4, MOV, AVI up to 100MB</p>
                      </div>
                    </div>
                  ) : (
                    <div
                      className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${isDragging ? "border-[#4F46E5] bg-indigo-50/50" : "border-gray-200 hover:border-gray-300"}`}
                      onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
                      onDragLeave={() => setIsDragging(false)}
                      onDrop={handleFileDrop}
                      onClick={() => fileRef.current?.click()}
                    >
                      <input ref={fileRef} type="file" accept=".mp4,.mkv,.avi,.mov,.webm,.mp3,.wav" className="hidden" onChange={e => { if (e.target.files?.[0]) setSelectedFile(e.target.files[0]); }} />
                      {selectedFile ? (
                        <div>
                          <Video size={28} className="mx-auto mb-3 text-[#4F46E5]" />
                          <p className="text-[14px] font-medium text-gray-800">{selectedFile.name}</p>
                          <p className="text-[12px] text-gray-400 mt-1">{(selectedFile.size / 1024 / 1024).toFixed(1)} MB</p>
                          <button onClick={e => { e.stopPropagation(); setSelectedFile(null); }} className="text-[12px] text-red-500 mt-2 hover:underline">Remove</button>
                        </div>
                      ) : (
                        <div>
                          <Upload size={28} className="mx-auto mb-3 text-gray-300" />
                          <p className="text-[14px] font-medium text-gray-600">Drop your video here or click to browse</p>
                          <p className="text-[12px] text-gray-400 mt-1">MP4, MKV, AVI, MOV, WebM, MP3, WAV</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Controls */}
              <div className="flex items-center gap-3 mt-5">
                <div className="flex-1">
                  <label className="text-[11px] font-medium text-gray-500 uppercase tracking-wide mb-1.5 block">Length</label>
                  <div className="relative">
                    <select
                      value={summaryLength}
                      onChange={e => setSummaryLength(e.target.value as SummaryLength)}
                      className="w-full h-10 px-3 pr-8 rounded-lg border border-gray-200 text-[13px] text-gray-700 appearance-none bg-white focus:outline-none focus:border-[#4F46E5] focus:ring-1 focus:ring-[#4F46E5]/20 cursor-pointer"
                    >
                      <option value="short">Short</option>
                      <option value="medium">Medium</option>
                      <option value="detailed">Detailed</option>
                    </select>
                    <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                  </div>
                </div>
                <div className="flex-1">
                  <label className="text-[11px] font-medium text-gray-500 uppercase tracking-wide mb-1.5 block">Style</label>
                  <div className="relative">
                    <select
                      value={summaryStyle}
                      onChange={e => setSummaryStyle(e.target.value as SummaryStyle)}
                      className="w-full h-10 px-3 pr-8 rounded-lg border border-gray-200 text-[13px] text-gray-700 appearance-none bg-white focus:outline-none focus:border-[#4F46E5] focus:ring-1 focus:ring-[#4F46E5]/20 cursor-pointer"
                    >
                      <option value="paragraph">Paragraph</option>
                      <option value="bullets">Bullet Points</option>
                    </select>
                    <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                  </div>
                </div>
              </div>

              {/* Error */}
              {error && (
                <div className="mt-4 p-3 rounded-lg bg-red-50 border border-red-200 text-[13px] text-red-600">
                  {error}
                </div>
              )}

              {/* Generate Button */}
              <button
                onClick={handleGenerate}
                disabled={isLoading}
                className="w-full h-11 mt-5 rounded-lg bg-[#4F46E5] text-white text-[14px] font-semibold hover:bg-[#4338CA] disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles size={16} />
                    Generate Summary
                  </>
                )}
              </button>
            </div>

            {/* ── RIGHT: Output Panel ── */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 flex flex-col">
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-[16px] font-semibold text-gray-900">Summary</h3>
                <div className="flex items-center gap-1">
                  <button onClick={handleCopy} className="flex items-center gap-1.5 px-3 h-8 rounded-md text-[12px] font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-colors">
                    <Copy size={13} />{copied ? "Copied!" : "Copy"}
                  </button>
                  <button onClick={handleDownload} className="flex items-center gap-1.5 px-3 h-8 rounded-md text-[12px] font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-colors">
                    <Download size={13} />Download
                  </button>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto">
                {summary ? (
                  <div className="animate-fade-in">
                    <p className="text-[14px] text-gray-700 leading-[1.7] mb-6 whitespace-pre-wrap">{summary}</p>
                    {keyPoints.length > 0 && (
                      <div>
                        <h4 className="text-[14px] font-semibold text-gray-900 mb-3">Key Points</h4>
                        <ul className="space-y-2">
                          {keyPoints.map((point, i) => (
                            <li key={i} className="flex items-start gap-2.5 text-[13px] text-gray-600 leading-[1.6]">
                              <span className="w-1.5 h-1.5 rounded-full bg-[#4F46E5] mt-[7px] flex-shrink-0" />
                              {point}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-center py-12">
                    <FileText size={32} className="text-gray-200 mb-3" />
                    <p className="text-[14px] text-gray-400 font-medium">No summary yet</p>
                    <p className="text-[12px] text-gray-300 mt-1">Generate one using the input panel</p>
                  </div>
                )}
              </div>

              {summary && (
                <div className="flex items-center justify-end pt-4 mt-4 border-t border-gray-100">
                  <div className="flex items-center gap-1.5 text-[12px] text-gray-400">
                    <Clock size={12} />
                    {readTime} min read
                  </div>
                </div>
              )}
            </div>
          </div>


        </div>
      </main>
    </div>
  );
}
