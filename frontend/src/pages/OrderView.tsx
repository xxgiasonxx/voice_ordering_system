import { XIcon } from '@/components/Icon';
import Header from '@/components/Header';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

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
  const baseURL = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:8000';
  const response = await fetch(`${baseURL}/see_order`, {
    credentials: 'include',
  });
  if (!response.ok) throw new Error('Failed to fetch order items');
  return response.json();
};

const OrderItemComponent = ({ item }: { item: OrderItem }) => (
  <div className="flex items-center gap-3 bg-white rounded-2xl p-4 shadow-card">
    <div className="flex flex-col justify-center overflow-hidden flex-1 min-w-0">
      <p className="text-[var(--color-text-primary)] text-sm font-semibold leading-normal line-clamp-1">
        {item.class} - {item.name}
      </p>
      <p className="text-[var(--color-text-secondary)] text-xs mt-0.5">
        數量: {item.quantity} | 單價: ${item.unitPrice}
      </p>
      {item.customization.note && item.customization.note !== '無' && (
        <p className="text-[var(--color-text-secondary)] text-xs mt-0.5">
          客製化: {item.customization.note} (+${item.customization.cus_price})
        </p>
      )}
    </div>
    <p className="text-[var(--color-text-primary)] text-sm font-bold whitespace-nowrap">
      ${item.subtotal}
    </p>
  </div>
);

const EmptyState = () => (
  <div className="flex flex-col items-center justify-center py-16 px-4">
    <div className="text-5xl mb-4">🛒</div>
    <p className="text-[var(--color-text-secondary)] text-base font-medium">目前沒有訂單項目</p>
    <Link
      to="/menu"
      className="mt-4 text-[var(--color-primary)] font-semibold hover:underline"
    >
      前往菜單
    </Link>
  </div>
);

function OrderSummaryScreen() {
  const navigate = useNavigate();
  const [orderItems, setOrderItems] = useState<OrderItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOrderItems = async () => {
      try {
        const response = await SeeOrderAPI();
        setOrderItems(response.order_state.items || []);
        const calculatedTotal = (response.order_state.items || []).reduce(
          (sum: number, item: OrderItem) => sum + item.subtotal,
          0
        );
        setTotal(calculatedTotal);
      } catch (err) {
        console.error('Error loading order items:', err);
        setError('載入訂單失敗');
      } finally {
        setIsLoading(false);
      }
    };
    fetchOrderItems();
  }, []);

  return (
    <div className="relative flex min-h-screen flex-col bg-[var(--color-background)]">
      <Header
        title="訂單明細"
        leftIcon={<XIcon />}
        onLeftClick={() => navigate('/menu')}
      />

      <div className="flex-1 px-4 py-4">
        {isLoading && (
          <div className="flex justify-center items-center py-16">
            <div className="w-8 h-8 border-2 border-[var(--color-border)] border-t-[var(--color-primary)] rounded-full animate-spin" />
          </div>
        )}

        {error && (
          <div className="mx-4 p-4 bg-[var(--color-error)]/10 text-[var(--color-error)] rounded-2xl text-sm font-medium">
            {error}
          </div>
        )}

        {!isLoading && !error && orderItems.length === 0 && <EmptyState />}

        {!isLoading && orderItems.length > 0 && (
          <div className="space-y-3">
            {orderItems.map((item) => (
              <OrderItemComponent key={item.id} item={item} />
            ))}
          </div>
        )}
      </div>

      {orderItems.length > 0 && (
        <div className="px-4 py-6 border-t border-[var(--color-border)] bg-white space-y-4 safe-bottom">
          <div className="flex justify-between items-center text-lg font-bold px-4 py-3 bg-[var(--color-primary-light)] rounded-2xl">
            <span>總計</span>
            <span className="text-[var(--color-primary)]">${total}</span>
          </div>
          <Link
            to="/payment"
            className="flex items-center justify-center w-full h-14 bg-[var(--color-primary)] text-white text-base font-bold rounded-2xl hover:bg-[var(--color-primary-hover)] active:scale-97 transition-all shadow-lg"
          >
            選擇結帳方式
          </Link>
        </div>
      )}
    </div>
  );
}

export default OrderSummaryScreen;