import Sidebar from "./Sidebar";
import TopBar from "./TopBar";

export default function Layout({ title, children }) {
  return (
    <div className="flex min-h-screen bg-base-900">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar title={title} />
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
