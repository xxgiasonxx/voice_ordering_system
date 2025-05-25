import { useState } from "react";
import { ArrowLeftIcon, MagnifyingGlassIcon, HouseIcon, ListIcon, ReceiptIcon, UserIcon } from "@/components/Icon";

// Data for menu items (in a real app, this would likely come from an API or state management)
const menuItemsData = [
  {
    category: "Popular",
    name: "Spicy Chicken Wings",
    description: "Marinated chicken wings with a spicy kick, served with a side of ranch dressing.",
    price: "$9.99",
    imageUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuCQl2BWHNipbWG-qy4lGVcMA08IGyE8hvmpA_xSS-XnRY_jKYdqAL9AcPooadBkwDXS4dh3cOh7iUJYm1hIMWe6L5Sd849E3DdrljECoK-efFkzA06EFxgJJh-EptRRlES0JJo8eIn_jTnDCK322aQ4f-H1gEWXVG1H5QnIUUojyQLyobRlPA2HLqoFjtQ4bgbR4RlnFLmTbeRYv-LdF3NPQYLLR5qylfYItr0PNS7qYqFLWGn9552JAR8gE_7y9zxT86S4QByEbhc", // Placeholder
  },
  {
    category: "Popular", // Assuming category is repeated for display logic, adjust as needed
    name: "Caesar Salad",
    description: "Crisp romaine lettuce, parmesan cheese, croutons, and Caesar dressing.",
    price: "$7.99",
    imageUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuCI8_HSbhhZ9gIN_RJ5tVeOuheFYXWAxt-A8tFIdukVUUq3EF8l1bjQHwuO_K3ykuVF6C0UzC-wn-zJHzSZ6Nu2JVCOmeJM-2DqpaJeFMcgVVLn3Usaul1nWZeVPSuxEPHke2pwI4Pe7xAT73nk4ikKeqVw0Sif6cB-IFyp7ktwGeh6mM5s_vozkdWzbxOnzBGL4Aq3AB8-MR7YO7iJy-UWUNZjuYvbaJ2VfmfKOuTguR5pn07_RPze1cJpZsf7uvVqZKaKchqKaME", // Placeholder
  },
  {
    category: "Popular",
    name: "Margherita Pizza",
    description: "Classic pizza with fresh mozzarella, basil, and tomato sauce.",
    price: "$12.99",
    imageUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuBLGFq9Z9tvqgL_dQ4l7rzkj7ccizZsxr5FsLAEnXbTpFvIBxAUlPlc2iK7mBSdEsOWuC4VHIlvsU2pFvTplQT-WVo3DDMThdVCr4oGw1MyHmD_76QrsK7WZQdAmVaBQ4DlN5zVcwVI0qm8nIiYaUupcZ-eD24DwHEGDUAyaT3xXkA5jPL73WA2CBOfmi8hlyy7Z786N9pjCd6ip4X-8TnCeZkbVEMLUpicbdqpI2r1kWbO9h_6ENoyTcda485sWcIne9uTb9DOnmQ", // Placeholder
  },
];

const MenuScreen = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState('Popular'); // To manage active tab

  // In a real Vite + React app, font links are in public/index.html or main.css
  // Tailwind CSS script is handled by the build process.
  // Title and favicon are in public/index.html.

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
    // Add search logic here if needed
  };

  const tabs = ["Popular", "Appetizers", "Main Courses", "Desserts"];

  return (
    <div
      className="relative flex size-full min-h-screen flex-col bg-slate-50 justify-between group/design-root overflow-x-hidden"
      style={{ fontFamily: '"Plus Jakarta Sans", "Noto Sans", sans-serif' }}
    >
      <div>
        {/* Header */}
        <div className="flex items-center bg-slate-50 p-4 pb-2 justify-between">
          <div className="text-[#0d141c] flex size-12 shrink-0 items-center" data-icon="ArrowLeft" data-size="24px" data-weight="regular">
            <ArrowLeftIcon />
          </div>
          <h2 className="text-[#0d141c] text-lg font-bold leading-tight tracking-[-0.015em] flex-1 text-center pr-12">Menu</h2>
        </div>

        {/* Search Bar */}
        <div className="px-4 py-3">
          <label className="flex flex-col min-w-40 h-12 w-full">
            <div className="flex w-full flex-1 items-stretch rounded-xl h-full">
              <div
                className="text-[#49739c] flex border-none bg-[#e7edf4] items-center justify-center pl-4 rounded-l-xl border-r-0"
                data-icon="MagnifyingGlass"
                data-size="24px"
                data-weight="regular"
              >
                <MagnifyingGlassIcon />
              </div>
              <input
                placeholder="Search for dishes"
                className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-xl text-[#0d141c] focus:outline-0 focus:ring-0 border-none bg-[#e7edf4] focus:border-none h-full placeholder:text-[#49739c] px-4 rounded-l-none border-l-0 pl-2 text-base font-normal leading-normal"
                value={searchTerm}
                onChange={handleSearchChange} // Added for controlled input
              />
            </div>
          </label>
        </div>

        {/* Tabs */}
        <div className="pb-3">
          <div className="flex border-b border-[#cedbe8] px-4 gap-8 overflow-x-auto"> {/* Added overflow-x-auto for smaller screens */}
            {tabs.map((tabName) => (
              <a // Consider using <button> or a div with onClick for better accessibility if not a real navigation
                key={tabName}
                className={`flex flex-col items-center justify-center border-b-[3px] pb-[13px] pt-4 cursor-pointer whitespace-nowrap ${ // Added cursor-pointer and whitespace-nowrap
                  activeTab === tabName
                    ? "border-b-[#0c7ff2] text-[#0d141c]"
                    : "border-b-transparent text-[#49739c]"
                }`}
                href="#" // In a real app, this would change state or route
                onClick={(e) => {
                  e.preventDefault(); // Prevent page reload
                  setActiveTab(tabName);
                }}
              >
                <p className={`text-sm font-bold leading-normal tracking-[0.015em] ${
                    activeTab === tabName ? "text-[#0d141c]" : "text-[#49739c]"
                }`}>{tabName}</p>
              </a>
            ))}
          </div>
        </div>

        {/* Menu Items Section */}
        {/* This part should be dynamic based on the activeTab and searchTearm */}
        {menuItemsData
          .filter(item => item.category === activeTab) // Filter items by their category matching the activeTab
          .filter(item => item.name.toLowerCase().includes(searchTerm.toLowerCase())) // Simple search filter
          .map((item, index) => (
          <div className="p-4" key={index}>
            <div className="flex items-stretch justify-between gap-4 rounded-xl">
              <div className="flex flex-[2_2_0px] flex-col gap-4">
                <div className="flex flex-col gap-1">
                  <p className="text-[#49739c] text-sm font-normal leading-normal">{item.category}</p>
                  <p className="text-[#0d141c] text-base font-bold leading-tight">{item.name}</p>
                  <p className="text-[#49739c] text-sm font-normal leading-normal">{item.description}</p>
                </div>
                <button
                  className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-xl h-8 px-4 flex-row-reverse bg-[#e7edf4] text-[#0d141c] text-sm font-medium leading-normal w-fit"
                >
                  <span className="truncate">{item.price}</span>
                </button>
              </div>
              <div
                className="w-full bg-center bg-no-repeat aspect-video bg-cover rounded-xl flex-1"
                style={{ backgroundImage: `url("${item.imageUrl}")` }}
              ></div>
            </div>
          </div>
        ))}
        {/* Add more sections or map over data for different categories */}

      </div>

      {/* Bottom Navigation */}
      <div>
        <div className="flex gap-2 border-t border-[#e7edf4] bg-slate-50 px-4 pb-3 pt-2">
          <a className="just flex flex-1 flex-col items-center justify-end gap-1 text-[#49739c]" href="#">
            <div className="text-[#49739c] flex h-8 items-center justify-center" data-icon="House" data-size="24px" data-weight="regular">
              <HouseIcon />
            </div>
            <p className="text-[#49739c] text-xs font-medium leading-normal tracking-[0.015em]">Home</p>
          </a>
          <a className="just flex flex-1 flex-col items-center justify-end gap-1 rounded-full text-[#0d141c]" href="#"> {/* This is the active one */}
            <div className="text-[#0d141c] flex h-8 items-center justify-center" data-icon="List" data-size="24px" data-weight="fill">
              <ListIcon />
            </div>
            <p className="text-[#0d141c] text-xs font-medium leading-normal tracking-[0.015em]">Menu</p>
          </a>
          <a className="just flex flex-1 flex-col items-center justify-end gap-1 text-[#49739c]" href="#">
            <div className="text-[#49739c] flex h-8 items-center justify-center" data-icon="Receipt" data-size="24px" data-weight="regular">
              <ReceiptIcon />
            </div>
            <p className="text-[#49739c] text-xs font-medium leading-normal tracking-[0.015em]">Orders</p>
          </a>
          <a className="just flex flex-1 flex-col items-center justify-end gap-1 text-[#49739c]" href="#">
            <div className="text-[#49739c] flex h-8 items-center justify-center" data-icon="User" data-size="24px" data-weight="regular">
              <UserIcon />
            </div>
            <p className="text-[#49739c] text-xs font-medium leading-normal tracking-[0.015em]">Profile</p>
          </a>
        </div>
        <div className="h-5 bg-slate-50"></div>
      </div>
    </div>
  );
};

export default MenuScreen;