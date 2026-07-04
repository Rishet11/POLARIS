import { dataTapeCsvUrl } from "@/lib/api";

export default function ExportCsvButton() {
  return (
    <a
      href={dataTapeCsvUrl()}
      download
      className="inline-flex items-center h-9 px-3 rounded-[4px] border border-border-hairline bg-secondary text-[13px] font-medium text-secondary-foreground hover:bg-row-hover"
    >
      Export data tape (CSV)
    </a>
  );
}
