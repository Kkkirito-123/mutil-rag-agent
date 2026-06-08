import axios from 'axios';
import { JSDOM } from 'jsdom';
import { buildAxiosRequestOptions } from '../../utils/httpRequest.js';

export async function fetchLinuxDoArticle(url: string): Promise<{ content: string }> {
    const match = url.match(/\/topic\/(\d+)/);
    const topicId = match ? match[1] : null;

    if (!topicId) {
        throw new Error('Invalid URL: Cannot extract topic ID.');
    }
    const apiUrl = `https://linux.do/t/${topicId}.json`;

    const response = await axios.get(apiUrl, buildAxiosRequestOptions({
        headers: {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'no-cache',
            'discourse-track-view': 'true',
            'discourse-track-view-topic-id': `${topicId}`,
            'pragma': 'no-cache',
            'referer': 'https://linux.do/search',
            'sec-ch-ua': '"Chromium";v="112", "Google Chrome";v="112", "Not:A-Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
            'Host': 'linux.do',
            'Connection': 'keep-alive'
        }
    }));

    const cookedHtml = response.data?.post_stream?.posts?.[0]?.cooked || '';
    const dom = new JSDOM(cookedHtml);
    const plainText = dom.window.document.body.textContent?.trim() || '';

    return { content: plainText };
}
