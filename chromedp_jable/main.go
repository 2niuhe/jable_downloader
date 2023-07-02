package main

import (
	"context"
	"fmt"
	"log"
	"net/url"

	"github.com/chromedp/cdproto/cdp"
	"github.com/chromedp/cdproto/network"
	"github.com/chromedp/chromedp"
	"github.com/spf13/cobra"
	"golang.org/x/exp/slices"
)

func get_jable_res(page_url string, proxy string) {
	// create context
	p_url, _ := url.Parse(page_url)

	o := append(chromedp.DefaultExecAllocatorOptions[:],
		//... any options here
		//chromedp.ProxyServer("http://127.0.0.1:1087"),
		// chromedp.NoFirstRun,
		// chromedp.NoDefaultBrowserCheck,
		// chromedp.Headless,
		// chromedp.Flag("headless", false),
		chromedp.UserAgent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"),
	)

	if proxy != "" {
		o = append(o, chromedp.ProxyServer(proxy))
	}

	cx, cancel := chromedp.NewExecAllocator(context.Background(), o...)
	defer cancel()

	ctx, cancel := chromedp.NewContext(cx)
	defer cancel()

	var evens []network.RequestID
	chromedp.ListenTarget(ctx, func(ev interface{}) {
		switch ev := ev.(type) {
		case *network.EventRequestWillBeSent:
			uri, _ := url.Parse(ev.Request.URL)
			if uri.Path != p_url.Path {
				break
			}
			evens = append(evens, ev.RequestID)
		case *network.EventLoadingFinished:
			i := slices.Index(evens, ev.RequestID)
			if i < 0 {
				break
			}
			go func() {
				c := chromedp.FromContext(ctx)
				rbp := network.GetResponseBody(ev.RequestID)
				body, err := rbp.Do(cdp.WithExecutor(ctx, c.Target))
				if err != nil {
					fmt.Println(err)
				}

				body_str := string(body)

				fmt.Println(body_str)

			}()
		}
	})
	// run task list
	err := chromedp.Run(ctx,
		chromedp.Navigate(page_url),
		chromedp.WaitReady(`//*[@id="site-header"]`),
	)
	if err != nil {
		log.Fatal(err)
	}
}

func main() {

	var proxyURL string = ""

	rootCmd := &cobra.Command{
		Use:   "chromedp_download url",
		Short: "A command-line program to download jable videos document using Chromedp",
		Run: func(cmd *cobra.Command, args []string) {
			if len(args) != 1 {
				cmd.Usage()
				fmt.Println("Please provide a URL to download")
				return
			}

			get_jable_res(args[0], proxyURL)

		},
	}

	rootCmd.Flags().StringVar(&proxyURL, "proxy", "", "Proxy URL")

	if err := rootCmd.Execute(); err != nil {
		log.Fatal(err)
	}

}
