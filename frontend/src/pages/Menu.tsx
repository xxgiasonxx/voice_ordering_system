import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Badge, Button, QuantitySelector } from '@/components/DesignSystem';
import { ArrowLeftIcon, MagnifyingGlassIcon } from '@/components/Icon';
import { MicIcon } from '@/components/Icon';
import axios from 'axios';

interface MenuItem {
  id: number;
  class: string;
  name: string;
  price: number;
  add_egg: 0 | 1;
  cheese: 0 | 1;
  kimchi: 0 | 1;
  roast: 0 | 1;
  cheese_milk: 0 | 1;
  danish: 0 | 1;
  combo: string;
  vegetarian: 0 | 1;
  recommended: 0 | 1;
}
interface ComboItem { id: string; name: string; price: number; description: string; }
interface DrinkItem { id: string; class: string; name: string; M: number; L: number; }

interface CartItem {
  id: string;
  item_id: string;
  name: string;
  price: number;
  quantity: number;
  size?: 'M' | 'L';
  customizations?: string[];
  type: 'main' | 'combo' | 'drink';
}

const CATEGORY_TABS = ['台式蛋餅', '吐司', '漢堡', '飲料', '套餐'];
const ITEM_ICONS: Record<string, string> = {
  '台式蛋餅': '🥞', '吐司': '🍞', '漢堡': '🍔',
  '特調飲品': '🥤', '現打飲品': '🧃', '套餐': '🍱',
};
const getItemIcon = (cls: string) => ITEM_ICONS[cls] || '🍽️';
const fmt = (p: number) => `$${Math.round(p)}`;
const CUS_OPTIONS = [
  { key: 'add_egg', label: '加蛋', price: 10 }, { key: 'cheese', label: '起司', price: 10 },
  { key: 'kimchi', label: '泡菜', price: 10 }, { key: 'roast', label: '燒肉', price: 20 },
  { key: 'cheese_milk', label: '起司牛奶', price: 5 }, { key: 'danish', label: '山型丹麥', price: 10 },
];
const getCusPrice = (keys: string[]) => keys.reduce((s, k) => s + (CUS_OPTIONS.find(o => o.key === k)?.price || 0), 0);

const MenuScreen: React.FC = () => {
  const navigate = useNavigate();
  const [menuData, setMenuData] = useState<{ main: MenuItem[]; combos: ComboItem[]; drinks: DrinkItem[] }>({ main: [], combos: [], drinks: [] });
  const [activeTab, setActiveTab] = useState('台式蛋餅');
  const [search, setSearch] = useState('');
  const [cart, setCart] = useState<CartItem[]>([]);
  const [showCart, setShowCart] = useState(false);
  const [loading, setLoading] = useState(true);
  const [addConfirmId, setAddConfirmId] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);

  const base = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:8000';

  const getToken = async () => {
    if (token) return token;
    try {
      const resp = await axios.get(`${base}/get-token`, { withCredentials: true });
      const newToken = resp.data.encrypted_token;
      // 如果已經有 token ('Token already set')，就直接返回一個標記值
      if (!newToken) {
        return "already_set";
      }
      setToken(newToken);
      return newToken;
    } catch {
      return null;
    }
  };

  useEffect(() => {
    getToken();
    axios.get(`${base}/menu`).then(r => { setMenuData(r.data); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const apiCall = async (endpoint: string, data: object) => {
    const t = await getToken();
    if (!t) return null;
    try {
      const resp = await axios.post(`${base}${endpoint}`, data, { withCredentials: true });
      return resp.data;
    } catch {
      return null;
    }
  };

  const addToCartAPI = async (itemId: number, qty: number, customizations: string, customizationsPrice: number, _itemType: string) => {
    const result = await apiCall('/order/add-item', {
      item_id: itemId,
      quantity: qty,
      customization_note: customizations,
      customization_price: customizationsPrice,
    });
    return result;
  };

  const updateCartItemAPI = async (cartItemId: string, quantity: number) => {
    return apiCall('/order/update-item', { cart_item_id: cartItemId, quantity });
  };

  const removeCartItemAPI = async (cartItemId: string) => {
    return apiCall('/order/remove-item', { cart_item_id: cartItemId });
  };

  const doAdd = useCallback(async (item: CartItem) => {
    const itemId = parseInt(String(item.item_id));
    const customizations = item.customizations?.join('、') || '無';
    const customizationsPrice = item.customizations ? getCusPrice(item.customizations) : 0;

    setCart(prev => {
      const existSame = prev.find(i2 => i2.item_id === item.item_id && i2.type === item.type && i2.price === item.price);
      if (existSame) return prev.map(i2 => i2.item_id === item.item_id && i2.type === item.type && i2.price === item.price ? { ...i2, quantity: i2.quantity + item.quantity } : i2);
      return [...prev, item];
    });

    const result = await addToCartAPI(itemId, item.quantity, customizations, customizationsPrice, item.type);
    if (result?.item) {
      setCart(prev => prev.map(i => i.id === item.id ? { ...i, id: result.item.id } : i));
    }

    setAddConfirmId(item.id);
    setTimeout(() => setAddConfirmId(null), 1200);
  }, []);

  const filteredMain = menuData.main.filter(i => {
    const matchSearch = !search.trim() || i.name.includes(search) || i.class.includes(search);
    return matchSearch && i.class === activeTab;
  });

  const cartCount = cart.reduce((s, i) => s + i.quantity, 0);
  const cartTotal = cart.reduce((s, i) => s + i.price * i.quantity, 0);

  return (
    <div className="flex flex-col h-screen bg-[#FFFBF5]">
      {/* Header */}
      <div className="sticky top-0 z-20 bg-white border-b border-[#EDE8E1] px-4 pt-3 pb-2">
        <div className="flex items-center gap-3 mb-2">
          <Link to="/choice" className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-[#F5F3EF] transition-colors">
            <ArrowLeftIcon />
          </Link>
          <h1 className="flex-1 text-lg font-bold text-[#2D2A26] text-center pr-10">線上菜單</h1>
          <button onClick={() => navigate('/voiceorder')} className="relative w-10 h-10 flex items-center justify-center rounded-full hover:bg-[#F5F3EF] transition-colors">
            <MicIcon />
            {cartCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 w-5 h-5 bg-[#F5A623] text-white text-xs font-bold rounded-full flex items-center justify-center">
                {cartCount}
              </span>
            )}
          </button>
        </div>
        <div className="flex items-center gap-2 bg-[#F5F3EF] rounded-xl px-3 py-2.5 mb-2">
          <MagnifyingGlassIcon className="w-4 h-4 text-[#9C9690] shrink-0" />
          <input
            type="text" placeholder="搜尋餐點..." value={search} onChange={e => setSearch(e.target.value)}
            className="flex-1 bg-transparent text-sm text-[#2D2A26] placeholder:text-[#9C9690] outline-none"
          />
        </div>
        <div className="flex gap-1.5 overflow-x-auto pb-1 -mx-1 px-1 scrollbar-hide">
          {CATEGORY_TABS.map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)}
              className={`shrink-0 px-3.5 py-1.5 rounded-full text-sm font-semibold transition-all duration-200 ${activeTab === tab ? 'bg-[#F5A623] text-white shadow-sm' : 'bg-[#F5F3EF] text-[#6B6660] hover:bg-[#EDE8E1]'}`}>
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3 pb-24">
        {loading ? (
          <div className="flex items-center justify-center py-20 text-[#9C9690]">載入中...</div>
        ) : activeTab === '飲料' ? (
          menuData.drinks.map(item => (
            <DrinkCard key={item.id} item={item} onAdd={(size, qty) => doAdd({ id: `drink-${item.id}-${Date.now()}`, item_id: item.id, name: item.name, price: size === 'L' ? item.L : item.M, quantity: qty, size, type: 'drink' })} confirmed={addConfirmId === `drink-${item.id}-${Date.now()}`} />
          ))
        ) : activeTab === '套餐' ? (
          menuData.combos.map(item => (
            <ComboCard key={item.id} item={item} onAdd={qty => doAdd({ id: `combo-${item.id}-${Date.now()}`, item_id: item.id, name: item.name, price: item.price, quantity: qty, type: 'combo' })} confirmed={addConfirmId === `combo-${item.id}-${Date.now()}`} />
          ))
        ) : (
          filteredMain.map((item, i) => (
            <MainCard key={item.id} item={item} index={i} onAdd={(qty, cust, cp) => doAdd({ id: `main-${item.id}-${Date.now()}`, item_id: String(item.id), name: item.name, price: item.price + cp, quantity: qty, customizations: cust, type: 'main' })} confirmed={false} />
          ))
        )}
      </div>

      {/* Cart Bar */}
      {cart.length > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-[#EDE8E1] p-3 shadow-lg z-30">
          <div className="max-w-lg mx-auto">
            <button onClick={() => setShowCart(true)}
              className="w-full flex items-center justify-between bg-[#F5A623] text-white rounded-2xl px-5 py-3.5 font-semibold active:scale-98 transition-transform">
              <div className="flex items-center gap-2">
                <span className="bg-white/20 text-sm font-bold px-2 py-0.5 rounded-full">{cartCount}</span>
                <span>查看購物車</span>
              </div>
              <span>{fmt(cartTotal)}</span>
            </button>
          </div>
        </div>
      )}

      {/* Cart Drawer */}
      {showCart && (
        <CartDrawer
          items={cart}
          onClose={() => setShowCart(false)}
          onUpdateQty={async (id, q) => {
            if (q <= 0) {
              await removeCartItemAPI(id);
              setCart(prev => prev.filter(i => i.id !== id));
            } else {
              await updateCartItemAPI(id, q);
              setCart(prev => prev.map(i => i.id === id ? { ...i, quantity: q } : i));
            }
          }}
          onCheckout={() => { setShowCart(false); navigate('/orderview'); }}
        />
      )}
    </div>
  );
};

const MainCard: React.FC<{ item: MenuItem; index: number; onAdd: (qty: number, cust: string[], cp: number) => void; confirmed: boolean }> = ({ item, index, onAdd, confirmed }) => {
  const [show, setShow] = useState(false);
  const [qty, setQty] = useState(1);
  const [sel, setSel] = useState<string[]>([]);
  const cp = getCusPrice(sel);
  const hasCus = item.add_egg || item.cheese || item.kimchi || item.roast || item.cheese_milk || item.danish;
  return (
    <>
      <div className="bg-white rounded-2xl border border-[#EDE8E1] shadow-card overflow-hidden animate-slide-up" style={{ animationDelay: `${index * 40}ms` }}>
        <div className="flex gap-3 p-4">
          <div className="w-20 h-20 rounded-xl bg-[#FFF3E0] flex items-center justify-center text-3xl shrink-0">{getItemIcon(item.class)}</div>
          <div className="flex-1 min-w-0 flex flex-col justify-between py-0.5">
            <div>
              <div className="flex items-center gap-1.5 mb-0.5">
                {item.recommended === 1 && <Badge color="orange">推薦</Badge>}
                <span className="text-xs text-[#9C9690]">{item.class}</span>
              </div>
              <p className="font-semibold text-[#2D2A26]">{item.name}</p>
            </div>
            <div className="flex items-center justify-between mt-1.5">
              <span className="text-[#F5A623] font-bold">{fmt(item.price)}</span>
              <button onClick={() => hasCus ? (setShow(true), setQty(1), setSel([])) : onAdd(1, [], 0)}
                className="px-4 py-1.5 text-sm font-semibold text-white bg-[#F5A623] rounded-xl hover:bg-[#E8951A] active:scale-95 transition-all">
                {confirmed ? '✓ 已加入' : '加入'}
              </button>
            </div>
          </div>
        </div>
      </div>
      {show && (
        <div className="fixed inset-0 z-50 flex items-end">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setShow(false)} />
          <div className="relative w-full bg-white rounded-t-3xl p-5 pb-8 animate-slide-up">
            <div className="w-10 h-1 bg-[#D4CEC7] rounded-full mx-auto mb-4" />
            <h3 className="text-lg font-bold text-[#2D2A26] mb-1">{item.name}</h3>
            <p className="text-sm text-[#9C9690] mb-4">已選配料：{sel.length === 0 ? '無' : sel.map(k => CUS_OPTIONS.find(o => o.key === k)?.label).join('、')}</p>
            <div className="space-y-2 mb-4">
              {CUS_OPTIONS.filter(o => item[o.key as keyof MenuItem] === 1).map(opt => (
                <label key={opt.key} className={`flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-colors ${sel.includes(opt.key) ? 'border-[#F5A623] bg-[#FFF3E0]' : 'border-[#EDE8E1] bg-white'}`}>
                  <div className="flex items-center gap-3">
                    <div onClick={() => setSel(p => p.includes(opt.key) ? p.filter(k => k !== opt.key) : [...p, opt.key])}
                      className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${sel.includes(opt.key) ? 'border-[#F5A623] bg-[#F5A623]' : 'border-[#D4CEC7]'}`}>
                      {sel.includes(opt.key) && <svg width="10" height="8" viewBox="0 0 10 8" fill="none"><path d="M1 4L3.5 6.5L9 1" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>}
                    </div>
                    <span className="text-[#2D2A26] font-medium text-sm">{opt.label}</span>
                  </div>
                  <span className="text-[#F5A623] text-sm font-semibold">+{opt.price}元</span>
                </label>
              ))}
            </div>
            <div className="flex items-center gap-3">
              <QuantitySelector value={qty} onChange={setQty} />
              <Button variant="primary" fullWidth onClick={() => { onAdd(qty, sel, cp); setShow(false); }}>
                加入 · {fmt((item.price + cp) * qty)}
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

const DrinkCard: React.FC<{ item: DrinkItem; onAdd: (size: 'M' | 'L', qty: number) => void; confirmed: boolean }> = ({ item, onAdd, confirmed }) => {
  const [show, setShow] = useState(false);
  const [size, setSize] = useState<'M' | 'L'>('M');
  const [qty, setQty] = useState(1);
  const price = size === 'L' ? item.L : item.M;
  return (
    <>
      <div className="bg-white rounded-2xl border border-[#EDE8E1] shadow-card p-4">
        <div className="flex gap-3">
          <div className="w-20 h-20 rounded-xl bg-[#E3F2FD] flex items-center justify-center text-3xl shrink-0">{getItemIcon(item.class)}</div>
          <div className="flex-1">
            <p className="font-semibold text-[#2D2A26]">{item.name}</p>
            <p className="text-xs text-[#9C9690]">{item.class}</p>
            <div className="flex items-center justify-between mt-2">
              <div className="flex gap-2">
                <span className="text-sm text-[#6B6660]">M: {fmt(item.M)}</span>
                {item.L && <span className="text-sm text-[#6B6660]">L: {fmt(item.L)}</span>}
              </div>
              <button onClick={() => setShow(true)}
                className="px-4 py-1.5 text-sm font-semibold text-white bg-[#F5A623] rounded-xl hover:bg-[#E8951A] active:scale-95 transition-all">
                {confirmed ? '✓ 已加入' : '加入'}
              </button>
            </div>
          </div>
        </div>
      </div>
      {show && (
        <div className="fixed inset-0 z-50 flex items-end">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setShow(false)} />
          <div className="relative w-full bg-white rounded-t-3xl p-5 pb-8 animate-slide-up">
            <div className="w-10 h-1 bg-[#D4CEC7] rounded-full mx-auto mb-4" />
            <h3 className="text-lg font-bold text-[#2D2A26] mb-1">{item.name}</h3>
            <p className="text-sm text-[#9C9690] mb-4">選擇容量</p>
            <div className="flex gap-3 mb-4">
              {(['M', 'L'] as const).filter(s => s === 'M' || item.L).map(s => (
                <button key={s} onClick={() => setSize(s)}
                  className={`flex-1 py-3 rounded-xl border-2 font-semibold transition-all ${size === s ? 'border-[#F5A623] bg-[#FFF3E0] text-[#F5A623]' : 'border-[#EDE8E1] text-[#6B6660]'}`}>
                  {s === 'M' ? `中杯 ${fmt(item.M)}` : `大杯 ${fmt(item.L!)}`}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-3">
              <QuantitySelector value={qty} onChange={setQty} />
              <Button variant="primary" fullWidth onClick={() => { onAdd(size, qty); setShow(false); }}>
                加入 · {fmt(price * qty)}
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

const ComboCard: React.FC<{ item: ComboItem; onAdd: (qty: number) => void; confirmed: boolean }> = ({ item, onAdd, confirmed }) => (
  <div className="bg-white rounded-2xl border border-[#EDE8E1] shadow-card p-4">
    <div className="flex gap-3">
      <div className="w-20 h-20 rounded-xl bg-[#FFF3E0] flex items-center justify-center text-3xl shrink-0">🍱</div>
      <div className="flex-1">
        <div className="flex items-center gap-1.5 mb-0.5"><Badge color="blue">{item.id} 套餐</Badge></div>
        <p className="font-semibold text-[#2D2A26]">{item.name}</p>
        <p className="text-xs text-[#9C9690] mt-0.5">{item.description}</p>
        <div className="flex items-center justify-between mt-2">
          <span className="text-[#F5A623] font-bold">{fmt(item.price)}</span>
          <button onClick={() => onAdd(1)}
            className={`px-4 py-1.5 text-sm font-semibold rounded-xl transition-all active:scale-95 ${confirmed ? 'bg-[#34C759] text-white' : 'bg-[#F5A623] text-white hover:bg-[#E8951A]'}`}>
            {confirmed ? '✓ 已加入' : '加入'}
          </button>
        </div>
      </div>
    </div>
  </div>
);

const CartDrawer: React.FC<{ items: CartItem[]; onClose: () => void; onUpdateQty: (id: string, qty: number) => void; onCheckout: () => void }> = ({ items, onClose, onUpdateQty, onCheckout }) => {
  const total = items.reduce((s, i) => s + i.price * i.quantity, 0);
  return (
    <div className="fixed inset-0 z-50 flex items-end">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full bg-white rounded-t-3xl max-h-[80vh] flex flex-col animate-slide-up">
        <div className="p-5 pb-3">
          <div className="w-10 h-1 bg-[#D4CEC7] rounded-full mx-auto mb-3" />
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-[#2D2A26]">購物車</h3>
            <span className="text-sm text-[#9C9690]">{items.reduce((s, i) => s + i.quantity, 0)} 件</span>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto px-5 space-y-3 pb-3">
          {items.map(item => (
            <div key={item.id} className="flex items-center gap-3 py-2 border-b border-[#F0EDE8] last:border-0">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-[#2D2A26] truncate">{item.name}</p>
                <p className="text-xs text-[#9C9690]">
                  {item.size ? `大杯 / ${fmt(item.price)}` : fmt(item.price)}
                  {item.customizations?.length ? ` · ${item.customizations.join('、')}` : ''}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <QuantitySelector value={item.quantity} onChange={q => onUpdateQty(item.id, q)} size="sm" />
                <span className="text-sm font-semibold text-[#F5A623] w-16 text-right">{fmt(item.price * item.quantity)}</span>
              </div>
            </div>
          ))}
        </div>
        <div className="p-5 pt-3 border-t border-[#EDE8E1]">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[#6B6660]">小計</span>
            <span className="text-xl font-bold text-[#2D2A26]">{fmt(total)}</span>
          </div>
          <Button variant="primary" fullWidth size="lg" onClick={onCheckout}>前往結帳</Button>
        </div>
      </div>
    </div>
  );
};

export default MenuScreen;