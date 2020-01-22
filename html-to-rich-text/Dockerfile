FROM node:12.14.1-alpine
WORKDIR /html-to-rich-text
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD [ "npm", "start" ]