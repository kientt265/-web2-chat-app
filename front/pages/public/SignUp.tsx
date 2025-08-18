import { userService } from '../../services/api.ts';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { User } from '../../types';
import logo from '../../src/assets/LoGo.png';

function Signup() {
    const [formData, setFormData] = useState<User>({
        username: '',
        password: '',
        email: ''
    })
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const navigate = useNavigate();

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value,
        });
        setError(null);
    };

    const handleSumit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setLoading(true);

        try {
            const response = await userService.register(formData);

        } catch (err: any) {
            setError(err.response?.data?.message || 'Login failed. Please try again.');
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className='flex flex-col justify-center items-center h-screen gap-6'>
         <img src={logo} alt="" className="w-1/5 object-contain" />      
        <form onSubmit={handleSumit} className='flex flex-col gap-3 justify-center items-center w-full max-w-sm bg-white p-6 rounded-xl shadow-md '>
        {error && <div className="text-red-500 text-center">{error}</div>}
            <input className='p-3  border rounded' 
                type="text" 
                name="username" 
                placeholder="UserName" 
                value={formData.username}
                onChange={handleInputChange}
                required
            />
            <input className='p-3 border rounded' 
                    type="email" 
                    name="email" 
                    placeholder="Email"
                    value={formData.email}
                    onChange={handleInputChange}
                    required
            />
            <input className='p-3  border rounded' 
                type="password" 
                name="password" 
                placeholder="Password" 
                value={formData.password}
                onChange={handleInputChange}
                required
            />




            <button 
                    className='hover:bg-red-600 rounded cursor-pointer p-2 bg-blue-600' 
                    type="submit"
                    
                    >{loading ? 'Logging in...' : 'SignUp'}</button>
            <p className="text-center">
          You have an account?{' '}
          <a href="/" className="text-blue-600 hover:underline">
            Log In
          </a>
        </p>
        </form>
    </div>
    )
};

export default Signup;