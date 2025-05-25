import { Link } from "react-router-dom";

export default function UnsupportVoice() {
    return (
        <>
            <div className="flex flex-col items-center justify-center h-screen bg-gray-100">
                <h1 className="text-2xl font-bold text-red-600 mb-4">語音點餐功能不支援</h1>
                <p className="text-gray-700 mb-6">抱歉，您的瀏覽器或設備不支援語音點餐功能。</p>
                <p className="text-gray-500">請使用支援語音識別的瀏覽器或設備。</p>
                <div className="mx-auto mt-8 w-full max-w-md px-3">
                    <button className="flex justify-center items-center w-full h-14 bg-blue-500 text-white text-base font-bold rounded-xl hover:bg-blue-600 active:bg-blue-700 transition-colors duration-200 shadow-md">
                        <Link
                            to="/choice"
                            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                        >
                            返回選擇點餐方式
                        </Link>
                    </button>
                </div>
            </div>
        </>
    );
}