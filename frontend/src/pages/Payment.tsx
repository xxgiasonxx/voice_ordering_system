import { useEffect, useState } from 'react';
import { ArrowLeftIcon } from '@/components/Icon';
import Header from '@/components/Header';
import { useNavigate } from 'react-router-dom';

interface OrderItem {
  id: string;
  item_id: number | string;
  class: string;
  name: string;
  unitPrice: number;
  subtotal: number;
  quantity: number;
  customization: {
    cus_price: number;
    note: string;
  };
}

interface OrderSummaryValues {
  items: OrderItem[];
  order_id?: string;
  order_time?: string;
  order_type?: string;
  payment?: {
    method?: string;
    status?: string;
  };
  subtotal?: number;
  deliveryFee?: number;
  total_price?: number;
}

const PaymentScreen: React.FC = () => {
  const navigate = useNavigate();
  const [selectedPaymentMethod] = useState<string>('counter-payment');
  const [orderSummary, setOrderSummary] = useState<OrderSummaryValues>({
    items: [],
    subtotal: 0,
    deliveryFee: 0,
    total_price: 0,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const baseURL = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:8000';

  const fetchOrderSummary = async () => {
    try {
      const response = await fetch(`${baseURL}/see_order`, {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        setOrderSummary(data.order_state);
      }
    } catch (error) {
      console.error('Error fetching order summary:', error);
    }
  };

  useEffect(() => {
    fetchOrderSummary();
  }, []);

  const handlePaymentSubmission = async () => {
    setIsSubmitting(true);
    try {
      const [submitRes] = await Promise.all([
        fetch(`${baseURL}/submit_payment`, {
          method: 'POST',
          credentials: 'include',
        }),
        fetch(`${baseURL}/clean_cookie`, {
          method: 'POST',
          credentials: 'include',
        }),
      ]);

      if (submitRes.ok) {
        alert('感謝您的訂單！');
        navigate('/');
      } else {
        console.error('Payment submission failed');
      }
    } catch (error) {
      console.error('Error submitting payment:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const paymentOptions = [
    { id: 'counter-payment', value: 'counter-payment', label: '櫃台結帳', icon: '💳' },
    { id: 'electronic-payment', value: 'electronic-payment', label: '電子支付', icon: '📱' },
  ];

  return (
    <div className="relative flex min-h-screen flex-col bg-[var(--color-background)]">
      <Header
        title="付款"
        leftIcon={<ArrowLeftIcon />}
        onLeftClick={() => navigate('/orderview')}
      />

      <div className="flex-1 px-4 py-6 max-w-md mx-auto w-full">
        <h3 className="text-[var(--color-text-primary)] text-base font-bold mb-4">付款方式</h3>
        <div className="space-y-3">
          {paymentOptions.map((option) => (
            <label
              key={option.id}
              htmlFor={option.id}
              className={`flex items-center gap-4 rounded-2xl border-2 p-4 cursor-pointer transition-all ${
                selectedPaymentMethod === option.value
                  ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)]'
                  : 'border-[var(--color-border)] bg-white hover:border-[var(--color-border-strong)]'
              }`}
            >
              <div
                className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all ${
                  selectedPaymentMethod === option.value
                    ? 'border-[var(--color-primary)] bg-[var(--color-primary)]'
                    : 'border-[var(--color-border-strong)]'
                }`}
              >
                {selectedPaymentMethod === option.value && (
                  <div className="w-2 h-2 bg-white rounded-full" />
                )}
              </div>
              <span className="text-xl">{option.icon}</span>
              <span className="text-[var(--color-text-primary)] font-semibold text-sm">
                {option.label}
              </span>
            </label>
          ))}
        </div>

        <h3 className="text-[var(--color-text-primary)] text-base font-bold mt-8 mb-4">訂單摘要</h3>
        <div className="bg-white rounded-2xl border border-[var(--color-border)] overflow-hidden">
          {orderSummary.items?.map((item, idx) => (
            <div
              key={item.id}
              className={`flex justify-between items-start px-4 py-3 ${
                idx !== 0 ? 'border-t border-[var(--color-border)]' : ''
              }`}
            >
              <div className="flex-1">
                <p className="text-[var(--color-text-primary)] text-sm font-medium">
                  {item.class} - {item.name} x{item.quantity}
                </p>
                {item.customization.note && item.customization.note !== '無' && (
                  <p className="text-[var(--color-text-muted)] text-xs mt-0.5">
                    備註: {item.customization.note}
                  </p>
                )}
              </div>
              <p className="text-[var(--color-text-primary)] text-sm font-medium ml-4">
                ${item.subtotal}
              </p>
            </div>
          ))}

          {orderSummary.subtotal !== undefined && (
            <>
              <div className="border-t border-[var(--color-border)] mx-4" />
              <div className="flex justify-between px-4 py-3">
                <p className="text-[var(--color-text-secondary)] text-sm">小計</p>
                <p className="text-[var(--color-text-primary)] text-sm">${orderSummary.subtotal}</p>
              </div>
            </>
          )}

          <div className="border-t border-[var(--color-border)] mx-4" />
          <div className="flex justify-between items-center px-4 py-4 bg-[var(--color-primary-light)]">
            <p className="text-[var(--color-text-primary)] text-base font-bold">總計</p>
            <p className="text-[var(--color-primary)] text-xl font-bold">
              ${orderSummary.total_price}
            </p>
          </div>
        </div>
      </div>

      <div className="px-4 py-6 border-t border-[var(--color-border)] bg-white safe-bottom">
        <button
          disabled={isSubmitting}
          onClick={handlePaymentSubmission}
          className="flex items-center justify-center w-full h-14 bg-[var(--color-primary)] text-white text-base font-bold rounded-2xl hover:bg-[var(--color-primary-hover)] disabled:opacity-50 active:scale-97 transition-all shadow-lg"
        >
          {isSubmitting ? (
            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            `確認${selectedPaymentMethod === 'counter-payment' ? '櫃台結帳' : '電子支付'} $${orderSummary.total_price}`
          )}
        </button>
      </div>
    </div>
  );
};

export default PaymentScreen;