import icon from '@/assets/icon.png';

const QuickOrderWelcome = () => {
  return (
    <div
      className="relative flex size-full min-h-screen flex-col bg-slate-50 justify-between group/design-root overflow-x-hidden"
      style={{ fontFamily: '"Plus Jakarta Sans", "Noto Sans", sans-serif' }}
    >
      <div>
        <div className="@container">
          <div className="@[48px]:px-4 @[48px]:py-3">
            {/* <div
              className="w-full bg-center bg-no-repeat bg-cover flex flex-col justify-end overflow-hidden bg-slate-50 @[480px]:rounded-xl min-h-80"
              style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuAI3GI4ycX_8g24o0cctxes0ZPk-LyLhu1rj2KZWcF2UAC4bkgjm7btbdaY2j_BBuiGwn_CYZm81epV5em3gNX-jvRzEe0C8K9I1GdQcICYEc2HMsCX8FtOE4_reVLjkXzCzid2uB4Jvih869Tbg9U3unigV0i9ePqhNHwXCoLr0SzNLQx_ww5gijADD11khIYhfRfbnDzHEEHnvIYE4us35y81EMf2m02FOq98QCG6dXhVKCkQ17W6m-v7zAWRiggIwS8Yy3Fjj6k")' }}
            > */}
                <img src={icon} alt="" />
            {/* </div> */}
          </div>
        </div>
        <h2 className="text-[#0d141c] tracking-light text-[28px] font-bold leading-tight px-4 text-center pb-3 pt-5">
          歡迎來到語音點餐系統!
        </h2>
        <p className="text-[#0d141c] text-base font-normal leading-normal pb-3 pt-1 px-4 text-center">
          使用語音點餐系統，讓您輕鬆點餐，無需手動輸入菜單
        </p>
      </div>
      <div>
        <div className="flex px-4 py-3">
          <button
            className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-xl h-12 px-5 flex-1 bg-[#0c7ff2] text-slate-50 text-base font-bold leading-normal tracking-[0.015em]"
          >
            <span className="truncate">開始點餐</span>
          </button>
        </div>
        <div className="h-5 bg-slate-50"></div>
      </div>
    </div>
  );
};

export default QuickOrderWelcome;