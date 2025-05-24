import { Link, Outlet } from "react-router-dom";

export default function ErrorPage() {
  return (
    <>
      <div className="min-h-screen flex flex-col items-center justify-center px-4 bg-gray-50">
        <div className="text-center space-y-6">
          <div className="text-6xl">😵</div>
          <h1 className="text-2xl font-bold text-gray-800">頁面不存在</h1>
          <p className="text-gray-600">抱歉，找不到您要的頁面</p>
          <Link 
            to="/" 
            className="inline-block bg-blue-500 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-600 transition-colors"
          >
            回到首頁
          </Link>
        </div>
      </div>
      <Outlet />
    </>
  );
}