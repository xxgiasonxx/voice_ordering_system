import { XIcon } from '@/components/Icon'
import axios from 'axios';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

// Define types for better type safety
interface Customization {
  cus_price: number;
  note: string;
}

interface OrderItem {
  id: string;
  item_id: number | string;
  class: string;
  name: string;
  unitPrice: number;
  subtotal: number;
  quantity: number;
  customization: Customization;
}

interface ApiResponse {
  order_state: {
    items: OrderItem[];
  };
}



const SeeOrderAPI = async (): Promise<ApiResponse> => {
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  const response = await axios.get<ApiResponse>(`${baseURL}/see_order`, {
    withCredentials: true,
  });
  
  if (response.status !== 200) {
    throw new Error('Failed to fetch order items');
  }
  
  return response.data;
};

// Component for a single order item
const OrderItemComponent = ({ item }: { item: OrderItem }) => (
  <div className="flex items-center gap-3 sm:gap-4 bg-white rounded-lg shadow-sm mx-4 px-4 sm:px-6 min-h-[72px] sm:min-h-[80px] py-4 justify-between mb-3">
    <div className="flex flex-col justify-center overflow-hidden flex-1 min-w-0">
      <p className="text-[#0d141c] text-sm sm:text-base font-medium leading-normal line-clamp-1">
        {item.class} - {item.name}
      </p>
      <p className="text-[#49739c] text-xs sm:text-sm font-normal leading-normal line-clamp-2 mt-1">
        數量: {item.quantity} | 單價: ${item.unitPrice}
      </p>
      {item.customization.note !== "無" && (
        <p className="text-[#49739c] text-xs sm:text-sm font-normal leading-normal line-clamp-2 mt-1">
          客製化: {item.customization.note} (+${item.customization.cus_price})
        </p>
      )}
    </div>
    <div className="shrink-0 ml-3">
      <p className="text-[#0d141c] text-sm sm:text-base font-semibold leading-normal whitespace-nowrap">
        ${item.subtotal}
      </p>
    </div>
  </div>
);

const LoadingSpinner = () => (
  <div className="flex justify-center items-center py-12 px-4">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    <span className="ml-3 text-gray-600">載入中...</span>
  </div>
);

const EmptyState = () => (
  <div className="text-center py-12 px-4 text-gray-500">
    <p className="text-lg">目前沒有訂單項目</p>
  </div>
);

function OrderSummaryScreen() {
  const [orderItems, setOrderItems] = useState<OrderItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOrderItems = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const response = await SeeOrderAPI();
        setOrderItems(response.order_state.items || []);
      } catch (error) {
        console.error('Error loading order items:', error);
        setError('載入訂單失敗，使用預設資料');
      } finally {
        setIsLoading(false);
      }
    };

    fetchOrderItems();
  }, []);

  useEffect(() => {
    const calculatedTotal = orderItems.reduce((sum, item) => sum + item.subtotal, 0);
    setTotal(calculatedTotal);
  }, [orderItems]);


  const renderContent = () => {
    if (isLoading) {
      return <LoadingSpinner />;
    }

    if (error) {
      return (
        <div className="text-center py-6 px-4">
          <p className="text-red-500 mb-2">{error}</p>
        </div>
      );
    }

    if (orderItems.length === 0) {
      return <EmptyState />;
    }

    return (
      <div className="py-4">
        {orderItems.map((item) => (
          <OrderItemComponent key={item.id} item={item} />
        ))}
      </div>
    );
  };

  return (
    <div
      className="relative flex size-full min-h-screen flex-col bg-slate-50 justify-between group/design-root overflow-x-hidden"
      style={{ fontFamily: '"Plus Jakarta Sans", "Noto Sans", sans-serif' }}
    >
      <div className="flex-1">
        {/* Header */}
        <div className="flex items-center bg-slate-50 px-4 sm:px-6 py-4 pb-2 justify-between sticky top-0 z-10">
          <div className="text-[#0d141c] flex size-10 sm:size-12 shrink-0 items-center">
            <Link to="/voiceorder">
              <XIcon />
            </Link>
          </div>
          <h1 className="text-lg sm:text-xl font-semibold text-[#0d141c]">訂單明細</h1>
          <div className="size-10 sm:size-12"></div> {/* Spacer for center alignment */}
        </div>
        
        {/* Order Items List */}
        <div className="pb-4">
          {renderContent()}
        </div>
      </div>
      
      {/* Total and Submit Section */}
      <div className="px-4 sm:px-6 py-6 border-t border-slate-200 bg-white space-y-6">
        <div className="flex justify-between items-center text-lg sm:text-xl font-bold bg-slate-50 px-4 py-3 rounded-lg">
          <span>總計:</span>
          <span className="text-blue-600">${total}</span>
        </div>
        <button 
          disabled={orderItems.length === 0}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium py-4 px-6 rounded-xl transition-colors duration-200 text-lg shadow-lg"
        >
          <Link
            to="/payment"
          >
            選擇結帳方式
          </Link>
        </button>
      </div>
    </div>
  );
}

export default OrderSummaryScreen;