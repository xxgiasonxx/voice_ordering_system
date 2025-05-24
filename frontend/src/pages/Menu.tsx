import { useState } from "react";
// SVG Icons as React Components

const ArrowLeftIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" fill="currentColor" viewBox="0 0 256 256">
    <path d="M224,128a8,8,0,0,1-8,8H59.31l58.35,58.34a8,8,0,0,1-11.32,11.32l-72-72a8,8,0,0,1,0-11.32l72-72a8,8,0,0,1,11.32,11.32L59.31,120H216A8,8,0,0,1,224,128Z"></path>
  </svg>
);

const MagnifyingGlassIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" fill="currentColor" viewBox="0 0 256 256">
    <path d="M229.66,218.34l-50.07-50.06a88.11,88.11,0,1,0-11.31,11.31l50.06,50.07a8,8,0,0,0,11.32-11.32ZM40,112a72,72,0,1,1,72,72A72.08,72.08,0,0,1,40,112Z"></path>
  </svg>
);

const HouseIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" fill="currentColor" viewBox="0 0 256 256">
    <path d="M218.83,103.77l-80-75.48a1.14,1.14,0,0,1-.11-.11,16,16,0,0,0-21.53,0l-.11.11L37.17,103.77A16,16,0,0,0,32,115.55V208a16,16,0,0,0,16,16H96a16,16,0,0,0,16-16V160h32v48a16,16,0,0,0,16,16h48a16,16,0,0,0,16-16V115.55A16,16,0,0,0,218.83,103.77ZM208,208H160V160a16,16,0,0,0-16-16H112a16,16,0,0,0-16,16v48H48V115.55l.11-.1L128,40l79.9,75.43.11.1Z"></path>
  </svg>
);

const ListIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" fill="currentColor" viewBox="0 0 256 256">
    <path d="M224,120v16a8,8,0,0,1-8,8H40a8,8,0,0,1-8-8V120a8,8,0,0,1,8-8H216A8,8,0,0,1,224,120Zm-8,56H40a8,8,0,0,0-8,8v16a8,8,0,0,0,8,8H216a8,8,0,0,0,8-8V184A8,8,0,0,0,216,176Zm0-128H40a8,8,0,0,0-8,8V72a8,8,0,0,0,8,8H216a8,8,0,0,0,8-8V56A8,8,0,0,0,216,48Z"></path>
  </svg>
);

const ReceiptIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" fill="currentColor" viewBox="0 0 256 256">
    <path d="M72,104a8,8,0,0,1,8-8h96a8,8,0,0,1,0,16H80A8,8,0,0,1,72,104Zm8,40h96a8,8,0,0,0,0-16H80a8,8,0,0,0,0,16ZM232,56V208a8,8,0,0,1-11.58,7.15L192,200.94l-28.42,14.21a8,8,0,0,1-7.16,0L128,200.94,99.58,215.15a8,8,0,0,1-7.16,0L64,200.94,35.58,215.15A8,8,0,0,1,24,208V56A16,16,0,0,1,40,40H216A16,16,0,0,1,232,56Zm-16,0H40V195.06l20.42-10.22a8,8,0,0,1,7.16,0L96,199.06l28.42-14.22a8,8,0,0,1,7.16,0L160,199.06l28.42-14.22a8,8,0,0,1,7.16,0L216,195.06Z"></path>
  </svg>
);

const UserIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" fill="currentColor" viewBox="0 0 256 256">
    <path d="M230.92,212c-15.23-26.33-38.7-45.21-66.09-54.16a72,72,0,1,0-73.66,0C63.78,166.78,40.31,185.66,25.08,212a8,8,0,1,0,13.85,8c18.84-32.56,52.14-52,89.07-52s70.23,19.44,89.07,52a8,8,0,1,0,13.85-8ZM72,96a56,56,0,1,1,56,56A56.06,56.06,0,0,1,72,96Z"></path>
  </svg>
);

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