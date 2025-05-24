import icon from '@/assets/icon.png';
import { Link } from 'react-router-dom';

const QuickOrderWelcome = () => {
  return (
    <div
      className="relative flex h-screen flex-col bg-slate-50 justify-between overflow-x-hidden"
      style={{ fontFamily: '"Plus Jakarta Sans", "Noto Sans", sans-serif' }}
    >
      <div className="flex-1 flex flex-col justify-center items-center px-6 py-8">
        <div className="mb-8">
          <img src={icon} alt="" className="w-48 h-48 mx-auto" />
        </div>
        
        <h2 className="text-[#0d141c] text-2xl font-bold leading-tight text-center mb-4">
          歡迎來到語音點餐系統!
        </h2>
        
        <p className="text-[#0d141c] text-base font-normal leading-normal text-center max-w-sm">
          使用語音點餐系統，讓您輕鬆點餐無需手動輸入菜單
        </p>
      </div>

      <div className="px-6 pb-8">
        <Link
          to="/choice"
          className="flex items-center justify-center w-full h-14 bg-[#50b3ea] text-white text-base font-bold rounded-xl hover:bg-[#78cbf3] active:bg-[#faaf52] transition-colors duration-200 shadow-md"
        >
          開始點餐
        </Link>
      </div>
    </div>
  );
};

export default QuickOrderWelcome;
