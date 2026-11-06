import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({plugins:[react()],build:{rollupOptions:{output:{entryFileNames:'assets/app.js',assetFileNames:asset=>asset.name?.endsWith('.css')?'assets/app.css':'assets/[name]-[hash][extname]'}}},server:{proxy:{'/api':{target:'http://localhost:8000',changeOrigin:true},'/property':{target:'http://localhost:8000',changeOrigin:true},'/site':{target:'http://localhost:8000',changeOrigin:true},'/robots.txt':{target:'http://localhost:8000'},'/sitemap.xml':{target:'http://localhost:8000'}}}})
