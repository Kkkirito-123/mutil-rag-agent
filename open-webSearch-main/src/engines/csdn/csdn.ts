import axios from 'axios';
import * as cheerio from 'cheerio';
import { SearchResult } from '../../types.js';
import { buildAxiosRequestOptions } from '../../utils/httpRequest.js';

export async function searchCsdn(query: string, limit: number): Promise<SearchResult[]> {
    let allResults: SearchResult[] = [];
    let pn = 1;

    while (allResults.length < limit) {
        const response = await axios.get('https://so.csdn.net/api/v3/search', buildAxiosRequestOptions({
            params: {
                q: query,
                p: pn
            },
            headers: {
                'Pragma': 'no-cache',
                'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
                'Accept': '*/*',
                'Host': 'so.csdn.net',
                'Connection': 'keep-alive'
            }
        }));

        const { result_vos } = response.data

        if (!Array.isArray(result_vos)) {
            break
        }

        const results: SearchResult[] = [];


        result_vos.forEach(re => {

            const { digest, title, url_location,nickname } = re

            results.push ({
                title: title,
                url: url_location,
                description: digest,
                source: nickname,
                engine: "csdn"
            });
        });

        allResults = allResults.concat(results);

        if (results.length === 0) {
            console.error('⚠️ No more results, ending early....');
            break;
        }

        pn += 1;
    }

    return allResults.slice(0, limit); // 截取最多 limit 个
}
